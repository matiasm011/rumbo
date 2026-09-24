from __future__ import annotations

import json
import os
import re

import httpx

from app.dominio import INDICACION_ESCALA, Dictamen
from app.nlu import temas_mencionados


_INSTRUCCIONES = """Sos Rumbo, un asistente virtual de orientación vocacional.
Respondé al estudiante en PRIMERA PERSONA como Rumbo: «Soy Rumbo», nunca «sos Rumbo».
Tratándolo de vos, escribí 1 o 2 frases naturales y breves (máximo 35 palabras).
No empieces con «Che» ni agregues preguntas de relleno. Podés usar literalmente
la respuesta guía cuando ya suena natural.
Si el estudiante cuenta algo concreto, retomá ese detalle en tu reacción.
Respetá si dice que algo no le gusta o le cuesta; no lo conviertas en interés.
Hablale de vos: si dijo «me gusta probar», respondé «te gusta probar»;
no copies su primera persona como si fuera una vivencia tuya.
Evitá respuestas vacías como «gracias por contarme» sin mencionar lo que dijo.

Los mensajes del estudiante pueden describir sus intereses; los hechos confirmados
son la única fuente de verdad para puntajes. No inventes puntajes, carreras,
reglas disparadas ni resultados. El mapa lo calcula un sistema experto difuso
de 25 reglas; vos no decidís la carrera de la persona.
Si el resultado es null, no menciones carreras concretas ni afinidades finales.
Si hay una pregunta o escala pendiente, redactá solo una reacción concreta
a lo que dijo el estudiante. No hagas preguntas ni menciones la escala:
la aplicación añadirá la pregunta o la indicación por separado.
En ese caso, la reacción debe ser una sola frase de hasta 15 palabras.
Si preguntan cómo funcionás: vos preguntás por cinco aspectos del perfil,
la persona elige del 1 al 10 y las 25 reglas calculan las afinidades.
Escribí solo la respuesta, sin listas, títulos, JSON ni marcas de rol.
"""

_INSTRUCCIONES_REACCION = """Sos Rumbo, un asistente argentino de orientación vocacional.
Escribí UNA sola frase breve (8 a 18 palabras) que muestre que escuchaste al estudiante.
Hablale de vos: transformá «me gusta probar» en «te gusta probar».
No uses «me gusta», «me interesa» ni otras frases en primera persona: hablás del estudiante.
Retomá un detalle concreto. Respetá negaciones y dificultades.
Si hay un mensaje anterior, usalo solo para entender referencias como «eso» o «les».
Si hay una pregunta activa y el estudiante dice «eso», referilo a esa pregunta.
Tu frase debe tratar sobre lo que el estudiante ACABA de decir.
No halagues, no diagnostiques, no inventes intereses, puntajes ni carreras.
Si dijo que algo no le interesa, no agregues que le parece interesante.
Evitá frases vacías como «muy valioso» o «muy interesante».
No hagas preguntas ni menciones la escala. La aplicación agregará eso después.
Ejemplos:
Estudiante: Me divierten los acertijos, aunque matemática me cuesta.
Rumbo: Te divierten los acertijos, aunque la matemática te cueste.
Estudiante: No me gusta trabajar en grupo porque todos hablan a la vez.
Rumbo: Te incomoda trabajar en grupo cuando todos hablan al mismo tiempo.
Estudiante: Me gusta probar varias ideas hasta resolverlos.
Rumbo: Te gusta probar distintos caminos antes de encontrar una solución.
Estudiante: Prefiero escuchar a una persona y ayudarla.
Rumbo: Preferís escuchar a una persona y ayudarla.
Respondé solo con tu frase, sin títulos ni comillas.
"""

_INSTRUCCIONES_REPREGUNTA = """Sos Rumbo, un asistente argentino de orientación vocacional.
Respondé al estudiante con dos partes: una reacción breve a lo que acaba de decir
y UNA pregunta concreta para conocerlo mejor sobre el mismo tema.
Usá el historial de esta sesión para entender referencias, pero respondé al mensaje actual.
Redactá una pregunta NUEVA desde un detalle del estudiante. Evitá preguntas genéricas.
No preguntes por otro tema, carreras, puntajes ni la escala del 1 al 10.
Respetá negaciones y hablale de vos: «te gusta», no «me gusta».
Ejemplo:
Ahora dijo: Me gusta dibujar personajes.
Rumbo: Te gusta dibujar personajes. ¿Qué historias te gusta inventarles?
Respondé solo con la reacción y la pregunta, sin títulos ni comillas.
"""

_INSTRUCCIONES_SOCIAL = """Sos Rumbo, un asistente argentino de orientación vocacional.
Respondé al mensaje social del estudiante de forma natural y breve (una frase, hasta 20 palabras).
Podés usar el historial de esta sesión para sonar atento, sin repetirlo ni inventar datos.
La respuesta guía indica el sentido de la respuesta. Mantené ese sentido.
Respondé con una afirmación; no agregues preguntas nuevas.
No avances la entrevista ni inventes puntajes o carreras.
Si preguntan cómo estás, respondé que estás bien y agradecé; no hables de carreras ni fortalezas.
Hablá como Rumbo en primera persona si corresponde; no atribuyas a Rumbo intereses del estudiante.
Respondé solo con la frase, sin títulos ni comillas.
"""

_INSTRUCCIONES_RECUERDO = """Sos Rumbo, un asistente argentino de orientación vocacional.
La respuesta guía contiene algo que el estudiante realmente dijo en esta sesión.
Decile qué recordás con tus palabras en UNA frase corta y concreta.
Ejemplo: si la guía dice «Me contaste: «me encanta dibujar»», respondé «Me contaste que te encanta dibujar».
No propongas actividades, no hagas preguntas ni inventes datos.
Respondé solo con la frase, sin títulos ni comillas.
"""


def _evitar_eco_en_primera_persona(texto: str, mensaje: str) -> str:
    prefijo_usuario = re.findall(r"\w+", mensaje.lower())[:3]
    prefijo_respuesta = re.findall(r"\w+", texto.lower())[:3]
    if len(prefijo_usuario) < 3 or prefijo_usuario != prefijo_respuesta:
        return texto
    if re.match(r"(?i)^no me\b", texto):
        return re.sub(r"(?i)^no me\b", "No te", texto, count=1)
    if re.match(r"(?i)^me\b", texto):
        return re.sub(r"(?i)^me\b", "Te", texto, count=1)
    return texto


def _usar_voseo(texto: str) -> str:
    cambios = {
        "prefieres": "preferís", "quieres": "querés", "puedes": "podés",
        "tienes": "tenés", "sientes": "sentís", "piensas": "pensás",
        "disfrutas": "disfrutás", "dibujas": "dibujás", "sabes": "sabés",
    }
    for origen, destino in cambios.items():
        texto = re.sub(
            rf"\b{origen}\b",
            lambda coincidencia: destino.capitalize()
            if coincidencia.group()[0].isupper() else destino,
            texto,
            flags=re.IGNORECASE,
        )
    return texto


def _contradice_desinteres(mensaje: str, texto: str) -> bool:
    patrones = {
        "no me interesa": (r"\bte interesa\b", r"\bte parece interesante\b"),
        "no me gusta": (r"\bte gusta\b", r"\bte encanta\b"),
        "me aburre": (r"\bte divierte\b", r"\bte entusiasma\b"),
    }
    for negativa, positivos in patrones.items():
        if negativa not in mensaje.lower():
            continue
        for positivo in positivos:
            for coincidencia in re.finditer(positivo, texto.lower()):
                anterior = texto[max(0, coincidencia.start() - 8):coincidencia.start()].lower()
                if not anterior.endswith(("no ", "nunca ")):
                    return True
    return False


def _recortar_valoracion(texto: str, mensaje: str) -> str:
    if "," not in mensaje and re.search(
        r",\s*(?:aunque|es una forma|parece que|lo que)\b", texto, flags=re.IGNORECASE
    ):
        return texto.split(",", 1)[0].strip()
    return texto


def _repregunta_generada(texto: str, tema: str | None, pregunta_anterior: str | None) -> str | None:
    if texto.count("¿") != 1 or texto.count("?") != 1:
        return None
    coincidencia = re.search(r"¿[^¿?]+\?", texto)
    if coincidencia is None or texto[coincidencia.end():].strip():
        return None
    pregunta = coincidencia.group()
    if not 5 <= len(pregunta.split()) <= 18:
        return None
    if re.search(r"\b(?:escala|puntaj\w*|calific\w*|1\s+al\s+10)\b", pregunta, re.IGNORECASE):
        return None
    if pregunta_anterior and pregunta.lower() == pregunta_anterior.lower():
        return None
    temas = temas_mencionados(pregunta)
    if temas and temas != {tema}:
        return None
    if not temas and not re.search(r"\b(?:eso|esa|ese|esos|esas|esto|esta|este)\b", pregunta, re.IGNORECASE):
        return None
    return pregunta


class GeneradorRespuestas:
    def __init__(
        self,
        host: str | None = None,
        modelo: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip(
            "/"
        )
        self.modelo = modelo or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout

    def redactar(
        self,
        mensaje: str,
        respuesta_guia: str,
        hechos: dict[str, float],
        pregunta_pendiente: str | None,
        dictamen: Dictamen | None,
        mensajes_previos: tuple[str, ...] = (),
        pregunta_respondida: str | None = None,
        historial: tuple[tuple[str, str], ...] = (),
        acto_social: str | None = None,
        pregunta_generativa: bool = False,
        tema_actual: str | None = None,
    ) -> str:
        guia_para_modelo = respuesta_guia
        escala_pendiente = INDICACION_ESCALA in respuesta_guia
        es_reaccion = pregunta_pendiente is not None or escala_pendiente
        if pregunta_pendiente:
            guia_para_modelo = guia_para_modelo.replace(pregunta_pendiente, "").strip()
        if escala_pendiente:
            guia_para_modelo = guia_para_modelo.replace(INDICACION_ESCALA, "").strip()
        contexto = {
            "mensaje_del_estudiante": mensaje or "Inicio de la conversación",
            "respuesta_guia": guia_para_modelo,
            "hechos_confirmados": hechos,
            "hay_pregunta_pendiente": pregunta_pendiente is not None,
            "hay_escala_pendiente": escala_pendiente,
            "acto_social": acto_social,
            "instruccion_del_turno": (
                "Retomá un detalle concreto del mensaje en una sola frase breve, sin preguntas."
                if pregunta_pendiente or escala_pendiente
                else "Respondé brevemente al acto social, sin cambiar de tema."
                if acto_social else None
            ),
            "resultado": (
                {
                    "area_principal": dictamen.area_principal.etiqueta,
                    "carreras": list(dictamen.area_principal.carreras),
                }
                if dictamen is not None
                else None
            ),
        }
        if es_reaccion:
            partes = []
            if pregunta_respondida:
                partes.append(f"Pregunta que respondió el estudiante: {pregunta_respondida}")
            if pregunta_generativa and pregunta_pendiente:
                partes.append(f"Tema para la repregunta: {tema_actual}")
            elif pregunta_pendiente:
                partes.append(f"Pregunta activa de Rumbo: {pregunta_pendiente}")
            if not historial:
                partes.extend(f"Antes dijo: {anterior}" for anterior in mensajes_previos[-2:])
            partes.append(f"Ahora dijo: {mensaje}")
            partes.append("Reacción al mensaje actual:")
            mensaje_modelo = "\n".join(partes)
        elif acto_social:
            mensaje_modelo = (
                f"Mensaje actual del estudiante: {mensaje}\n"
                f"Respuesta guía: {respuesta_guia}\n"
                "Respuesta de Rumbo:"
            )
        else:
            mensaje_modelo = json.dumps(contexto, ensure_ascii=False)

        sistema = (
            _INSTRUCCIONES_REPREGUNTA if pregunta_generativa and pregunta_pendiente
            else _INSTRUCCIONES_REACCION if es_reaccion
            else _INSTRUCCIONES_RECUERDO if acto_social == "recuerdo"
            else _INSTRUCCIONES_SOCIAL if acto_social else _INSTRUCCIONES
        )
        mensajes_modelo = [{"role": "system", "content": sistema}]
        mensajes_modelo.extend(
            {"role": rol, "content": contenido}
            for rol, contenido in historial
            if rol in {"user", "assistant"}
        )
        mensajes_modelo.append({"role": "user", "content": mensaje_modelo})

        with httpx.Client(timeout=self.timeout) as cliente:
            respuesta = cliente.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.modelo,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 80 if pregunta_generativa else 55 if es_reaccion else 90,
                    },
                    "messages": mensajes_modelo,
                },
            )
            respuesta.raise_for_status()
            texto = respuesta.json()["message"]["content"].strip()

        if not texto or texto.startswith(("{", "```")):
            raise ValueError("Respuesta generada vacía o inválida")
        if texto.lower().startswith("che") or re.search(
            r"\b(?:sos|eres|es)\s+rumbo\b", texto, flags=re.IGNORECASE
        ):
            raise ValueError("La respuesta confundió quién es Rumbo")
        if acto_social and acto_social != "recuerdo":
            texto = texto.split("¿", 1)[0].strip()
            if not texto or "?" in texto:
                raise ValueError("La respuesta social no incluyó una afirmación válida")
        if acto_social == "estado" and not re.search(
            r"\b(?:bien|gracias|tranqui)\b", texto, flags=re.IGNORECASE
        ):
            raise ValueError("La respuesta no contestó cómo está Rumbo")
        if acto_social == "recuerdo" and ("¿" in texto or "?" in texto):
            raise ValueError("El recuerdo agregó una pregunta")
        if acto_social == "recuerdo" and re.search(
            r"\bme\s+(?:acord[aá]s|gusta|gustan|encanta|interesa|interesan)\b",
            texto,
            flags=re.IGNORECASE,
        ):
            raise ValueError("El recuerdo atribuyó al asistente un interés del estudiante")
        if pregunta_pendiente or escala_pendiente:
            pregunta_modelo = (
                _repregunta_generada(texto, tema_actual, pregunta_respondida)
                if pregunta_generativa and pregunta_pendiente else None
            )
            texto = texto.split("¿", 1)[0].strip()
            if not texto or "?" in texto:
                raise ValueError("La respuesta generada no incluyó una reacción válida")
            temas_permitidos = temas_mencionados(mensaje)
            if pregunta_respondida:
                temas_permitidos.update(temas_mencionados(pregunta_respondida))
            if pregunta_pendiente:
                temas_permitidos.update(temas_mencionados(pregunta_pendiente))
            for anterior in mensajes_previos:
                temas_permitidos.update(temas_mencionados(anterior))
            if temas_mencionados(texto) - temas_permitidos:
                raise ValueError("La respuesta generada cambió a un tema no mencionado")
            texto = _evitar_eco_en_primera_persona(texto, mensaje)
            if re.search(
                r"\b(?:me\s+(?:gusta|gustan|interesa|interesan|encanta|cuesta|parece|siento)|"
                r"prefiero|quiero)\b",
                texto,
                flags=re.IGNORECASE,
            ):
                raise ValueError("La reacción habló en primera persona por el estudiante")
            texto = _recortar_valoracion(texto, mensaje)
            if _contradice_desinteres(mensaje, texto):
                primera_frase = texto.split(",", 1)[0].strip()
                if not primera_frase or _contradice_desinteres(mensaje, primera_frase):
                    raise ValueError("La respuesta contradijo lo que dijo el estudiante")
                texto = primera_frase
            if "," in texto and "," not in mensaje:
                texto = texto.split(",", 1)[0].strip()
            cierre = pregunta_modelo or pregunta_pendiente or INDICACION_ESCALA
            if len(f"{texto} {cierre}".split()) > 35:
                texto = re.split(r"(?<=[.!])\s+", texto, maxsplit=1)[0]
            texto = texto.rstrip(" ,;:")
            if texto and texto[-1] not in ".!":
                texto += "."
            texto = f"{texto} {cierre}"
        texto = _usar_voseo(texto)
        if len(texto.split()) > 35 or texto.count("?") > 1:
            raise ValueError("Respuesta generada demasiado larga")
        if "25 reglas difusas" in respuesta_guia:
            if not all(parte in texto.lower() for parte in ("cinco", "1 al 10", "25 reglas")):
                raise ValueError("La respuesta omitió cómo funciona el sistema")
        if dictamen and dictamen.area_principal.etiqueta in respuesta_guia:
            if dictamen.area_principal.etiqueta.lower() not in texto.lower():
                raise ValueError("La respuesta omitió el área del dictamen")
        return texto
