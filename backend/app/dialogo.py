from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field, replace
from difflib import get_close_matches
from uuid import uuid4

from app.dominio import INDICACION_ESCALA, PREGUNTAS, VARIABLES, Dictamen, Perfil
from app.generador import GeneradorRespuestas
from app.motor_difuso import inferir
from app.nlu import detectar_tema, es_saludo


SALUDO = "¡Hola! Soy Rumbo. " + PREGUNTAS[VARIABLES[0]]
MAX_TURNOS_CONTEXTO = 24


@dataclass
class Sesion:
    id: str
    hechos: dict[str, float] = field(default_factory=dict)
    dictamen: Dictamen | None = None
    pregunta_actual: str | None = VARIABLES[0]
    esperando_detalle: bool = False
    esperando_escala: bool = False
    mensaje_actual: str = ""
    mensajes_tema: list[str] = field(default_factory=list)
    explorando_alternativas: int = 0
    historial: list[tuple[str, str]] = field(default_factory=list)
    pregunta_mostrada: str | None = None


_DESPEDIDAS = frozenset(
    {"chau", "chao", "adios", "hasta luego", "nos vemos", "hasta pronto", "me voy"}
)
_DUDAS = frozenset(
    {
        "no se", "nose", "ni idea", "no estoy seguro", "no estoy segura",
        "no lo se", "no se que decir", "mmm", "mm", "no se que estudiar",
        "estoy perdido", "estoy perdida", "me cuesta elegir",
    }
)
_GRACIAS = frozenset({"gracias", "muchas gracias", "genial", "buenisimo"})
_ESTADO = frozenset(
    {"como estas", "como andas", "como va", "todo bien", "que tal estas"}
)
_IDENTIDAD = frozenset(
    {"que sos", "quien sos", "que eres", "quien eres", "sos una ia", "sos un bot"}
)
_FUNCIONAMIENTO = frozenset(
    {
        "como funcionas", "como funciona", "como funciona esto",
        "como funciona rumbo", "como funciona tu sistema",
        "me explicas como funciona", "me explicas como funcionas",
        "que haces", "que podes hacer", "para que servis", "como me ayudas",
    }
)
_PREGUNTA_RECUERDO = re.compile(
    r"\b(?:te acordas|recordas|que te conte|que dije|que sabes de mi)\b"
)
_TEMAS = {
    "analitico": "lo analítico",
    "social": "lo social",
    "creativo": "lo creativo",
    "ciencias_vida": "las ciencias de la vida",
    "seguridad_laboral": "la estabilidad laboral",
}
_REPREGUNTAS = {
    "analitico": "¿Qué te suele pasar cuando tenés que resolver un problema o acertijo?",
    "social": "¿Qué te gusta o te cuesta al trabajar con otras personas?",
    "creativo": "¿Qué cosas te gusta crear o imaginar?",
    "ciencias_vida": "¿Hay algún tema de biología o salud que te dé curiosidad?",
    "seguridad_laboral": "¿Qué te haría sentir más tranquilo respecto al trabajo en el futuro?",
}


def _prefiere_otra_actividad(tema: str, mensaje: str) -> bool:
    texto = _normalizar(mensaje)
    return tema == "analitico" and "prefiero" in texto and any(
        frase in texto for frase in
        ("prefiero no", "no relacionado", "otra cosa", "algo diferente", "algo distinto")
    )


def _repregunta(tema: str, mensaje: str) -> str:
    texto = _normalizar(mensaje)
    if _prefiere_otra_actividad(tema, mensaje):
        return "¿Qué actividades o temas sí te interesan más?"
    if tema == "analitico" and "acertij" in texto:
        return "¿Qué disfrutás más de un acertijo: probar ideas o encontrar la respuesta?"
    if tema == "social" and ("grupo" in texto or "todos hablan" in texto):
        return "¿Te sentís más cómodo trabajando con alguien de a uno?"
    if tema == "creativo" and "personaj" in texto:
        return "¿Te gusta más diseñar esos personajes o inventarles historias?"
    if tema == "ciencias_vida" and any(
        frase in texto for frase in ("no me interesa", "no me gusta", "me aburre")
    ):
        return "¿Qué es lo que no te atrae de la biología o la salud?"
    return _REPREGUNTAS[tema]


def _acuse_contextual(tema: str, mensaje: str) -> str | None:
    texto = _normalizar(mensaje)
    if (
        tema == "analitico"
        and "me llevo bien" in texto
        and "prefiero no" in texto
        and "eso" in texto
    ):
        return "Entiendo: te llevás bien con los números, pero preferís no dedicarte a eso."
    if (
        _prefiere_otra_actividad(tema, mensaje)
        and "me llevo bien" in texto
        and "ellos" in texto
    ):
        return "Te llevás bien con los números, pero preferís dedicarte a otras cosas."
    return None


def _pregunta_vigente(sesion: Sesion) -> str:
    if sesion.pregunta_actual is None:
        return ""
    if sesion.esperando_detalle:
        if sesion.explorando_alternativas >= 3:
            return "¿Te atrae más crear, ayudar a otros, investigar o buscar estabilidad?"
        if sesion.explorando_alternativas == 2:
            return "¿Qué es lo que más te gusta de eso?"
        primero = sesion.mensajes_tema[0] if sesion.mensajes_tema else ""
        return _repregunta(sesion.pregunta_actual, primero)
    if sesion.pregunta_actual == "analitico" and sesion.hechos:
        return PREGUNTAS["analitico"].replace("Para empezar, ¿cómo", "¿Cómo", 1)
    return PREGUNTAS[sesion.pregunta_actual]


def _normalizar(texto: str) -> str:
    normalizado = texto.strip().lower()
    for vocal, base in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        normalizado = normalizado.replace(vocal, base)
    return " ".join(re.sub(r"[^\w\s]", " ", normalizado).split())


def _acto_social(texto: str) -> str | None:
    if _PREGUNTA_RECUERDO.search(texto):
        return "recuerdo"
    if es_saludo(texto):
        return "saludo"
    sin_saludo = re.sub(
        r"^(?:hola|buenas|hey|buenos dias|buenas tardes|buenas noches)\s+",
        "",
        texto,
    )
    if sin_saludo in _ESTADO or get_close_matches(sin_saludo, _ESTADO, n=1, cutoff=0.88):
        return "estado"
    if sin_saludo in _IDENTIDAD:
        return "identidad"
    if sin_saludo in _FUNCIONAMIENTO:
        return "funcionamiento"
    if texto in _DESPEDIDAS:
        return "despedida"
    if texto in _DUDAS:
        return "duda"
    if texto in _GRACIAS:
        return "agradecimiento"
    return None


def _valor_escrito(texto: str) -> int | None:
    if re.fullmatch(r"(?:10|[1-9])(?:\s+(?:de\s+)?10)?", texto):
        return int(texto.split()[0])
    return None


def _pendientes(hechos: dict[str, float]) -> tuple[str, ...]:
    return tuple(nombre for nombre in VARIABLES if nombre not in hechos)


@dataclass(frozen=True)
class Turno:
    respuesta: str
    sesion_id: str
    hechos: dict[str, float]
    pendientes: tuple[str, ...]
    dictamen: Dictamen | None
    usado_llm: bool
    escala_pendiente: str | None = None
    reglas_totales: int = 25


class Dialogo:
    def __init__(self, generador: GeneradorRespuestas | None = None) -> None:
        self.generador = generador
        self._sesiones: dict[str, Sesion] = {}

    def iniciar(self) -> Turno:
        sesion = Sesion(id=str(uuid4()))
        self._sesiones[sesion.id] = sesion
        return self._turno(sesion, SALUDO, generar=False)

    def responder(
        self, sesion_id: str | None, mensaje: str = "", valor: int | None = None
    ) -> Turno:
        sesion = self._sesiones.get(sesion_id or "")
        if sesion is None:
            sesion = Sesion(id=str(uuid4()))
            self._sesiones[sesion.id] = sesion
        return self._responder_impl(sesion, mensaje, valor)

    def responder_guia(
        self, sesion_id: str | None, mensaje: str = "", valor: int | None = None
    ) -> Turno:
        """Guía determinística instantánea, sin llamar al LLM.

        Corre sobre una copia de la sesión con un diálogo sin generador:
        no muta el estado real y devuelve el mismo texto que _turno usaría
        como guía. Sirve para mostrar algo al instante mientras se genera
        la versión final.
        """
        real = self._sesiones.get(sesion_id or "")
        if real is None:
            copia = Sesion(id=sesion_id or str(uuid4()))
        else:
            copia = copy.deepcopy(real)
        turno = Dialogo(generador=None)._responder_impl(copia, mensaje, valor)
        if real is None:
            return turno
        # La guía anticipa el texto; los hechos los confirma el turno final.
        return replace(
            turno,
            hechos=dict(real.hechos),
            pendientes=_pendientes(real.hechos),
            dictamen=real.dictamen,
            escala_pendiente=(
                real.pregunta_actual
                if real.esperando_escala and real.dictamen is None
                else None
            ),
        )

    def _responder_impl(
        self, sesion: Sesion, mensaje: str = "", valor: int | None = None
    ) -> Turno:
        if valor is not None:
            if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= 10:
                raise ValueError("El valor debe estar entre 1 y 10")
            sesion.mensaje_actual = (
                f"Elegí {valor} de 10 para {_TEMAS[sesion.pregunta_actual]}"
                if sesion.pregunta_actual else ""
            )
            return self._responder_valor(sesion, valor)

        mensaje = mensaje or ""
        sesion.mensaje_actual = mensaje
        texto = _normalizar(mensaje)
        acto = _acto_social(texto)

        if _pide_reinicio(mensaje):
            sesion.hechos.clear()
            sesion.dictamen = None
            sesion.pregunta_actual = VARIABLES[0]
            sesion.esperando_detalle = False
            sesion.esperando_escala = False
            sesion.mensajes_tema.clear()
            sesion.explorando_alternativas = 0
            sesion.historial.clear()
            sesion.pregunta_mostrada = None
            return self._turno(
                sesion,
                "Dale, empecemos de nuevo. " + PREGUNTAS[VARIABLES[0]],
                generar=False,
            )

        if sesion.dictamen is not None:
            if acto in {"saludo", "estado", "identidad", "funcionamiento", "recuerdo"}:
                return self._responder_social(sesion, acto)
            if acto == "despedida":
                return self._turno(sesion, "¡Chau! Si querés otro resultado, decime «reiniciar».")
            if acto == "agradecimiento":
                return self._turno(sesion, "¡De nada! Si querés otro perfil, decime «reiniciar».")
            return self._turno(
                sesion, "Tu mapa es un punto de partida. Para probar otro perfil, decime «reiniciar»."
            )

        if acto is not None:
            return self._responder_social(sesion, acto)

        if sesion.esperando_escala:
            numero = _valor_escrito(texto)
            if numero is not None:
                return self._responder_valor(sesion, numero)
            return self._turno(
                sesion,
                "Elegí una opción del 1 al 10 en la escala de abajo para seguir.",
                generar=False,
            )

        if not texto or _valor_escrito(texto) is not None:
            return self._turno(
                sesion,
                "Primero contame con tus palabras. "
                + (sesion.pregunta_mostrada or _pregunta_vigente(sesion)),
                generar=False,
            )

        if not sesion.esperando_detalle:
            pregunta_respondida = sesion.pregunta_mostrada or _pregunta_vigente(sesion)
            tema = detectar_tema(mensaje, _pendientes(sesion.hechos), sesion.pregunta_actual)
            if tema is not None:
                sesion.pregunta_actual = tema
            sesion.mensajes_tema = [mensaje]
            sesion.esperando_detalle = True
            sesion.explorando_alternativas = int(
                _prefiere_otra_actividad(sesion.pregunta_actual, mensaje)
            )
            acuse = _acuse_contextual(sesion.pregunta_actual, mensaje)
            return self._turno(
                sesion,
                (acuse or "Te escucho.") + " " + _pregunta_vigente(sesion),
                pregunta_respondida=pregunta_respondida,
            )

        pregunta_respondida = sesion.pregunta_mostrada or _pregunta_vigente(sesion)
        tema = detectar_tema(mensaje, _pendientes(sesion.hechos), sesion.pregunta_actual)
        if tema is not None and tema != sesion.pregunta_actual:
            sesion.pregunta_actual = tema
            sesion.mensajes_tema = [mensaje]
            sesion.explorando_alternativas = 0
            return self._turno(
                sesion,
                "Entiendo, cambiemos de tema. " + _pregunta_vigente(sesion),
                pregunta_respondida=pregunta_respondida,
            )

        if tema == sesion.pregunta_actual and sesion.explorando_alternativas:
            sesion.explorando_alternativas = 0
            sesion.mensajes_tema = [mensaje]
            return self._turno(
                sesion,
                "Entiendo. " + _pregunta_vigente(sesion),
                pregunta_respondida=pregunta_respondida,
            )

        if sesion.explorando_alternativas:
            sesion.mensajes_tema.append(mensaje)
            sesion.explorando_alternativas += 1
            return self._turno(
                sesion,
                _pregunta_vigente(sesion),
                pregunta_respondida=pregunta_respondida,
            )

        # La charla orienta el tema; solo la escala registra un hecho.
        sesion.mensajes_tema.append(mensaje)
        sesion.esperando_detalle = False
        sesion.esperando_escala = True
        sesion.explorando_alternativas = 0
        return self._turno(
            sesion,
            "Ahora lo entiendo un poco mejor. " + INDICACION_ESCALA,
            pregunta_respondida=pregunta_respondida,
        )

    def _responder_valor(self, sesion: Sesion, valor: int) -> Turno:
        if sesion.dictamen is not None:
            return self._turno(sesion, "Tu mapa ya está listo. Si querés otro, decime «reiniciar».")
        if not sesion.esperando_escala:
            return self._turno(
                sesion,
                "Primero contame con tus palabras. "
                + (sesion.pregunta_mostrada or _pregunta_vigente(sesion)),
                generar=False,
            )

        clave = sesion.pregunta_actual
        sesion.hechos[clave] = float(valor)
        sesion.esperando_detalle = False
        sesion.esperando_escala = False
        pendientes = _pendientes(sesion.hechos)
        if not pendientes:
            sesion.pregunta_actual = None
            sesion.dictamen = inferir(Perfil.from_mapping(sesion.hechos))
            area = sesion.dictamen.area_principal.etiqueta
            return self._turno(
                sesion,
                f"Con tus respuestas, {area} aparece como una opción para explorar. "
                "Mirá tu mapa para ver por qué.",
            )

        sesion.pregunta_actual = pendientes[0]
        return self._turno(
            sesion,
            f"Anotado: {valor}/10. {_pregunta_vigente(sesion)}",
            generar=False,
        )

    def _responder_social(self, sesion: Sesion, acto: str) -> Turno:
        pregunta = sesion.pregunta_mostrada or _pregunta_vigente(sesion)
        hay_recuerdos = False
        if acto == "saludo":
            respuesta = (
                "¡Hola! Cuando quieras, elegí un número en la escala."
                if sesion.esperando_escala
                else "¡Hola! Te escucho."
            )
        elif acto == "estado":
            respuesta = (
                "¡Bien, gracias por preguntar! La escala sigue acá cuando quieras."
                if sesion.esperando_escala
                else "¡Bien, gracias por preguntar! Estoy listo para charlar."
            )
        elif acto == "identidad":
            respuesta = (
                "Soy Rumbo, un asistente de orientación vocacional. "
                "Te ayudo a explorar opciones según lo que te gusta."
            )
        elif acto == "funcionamiento":
            respuesta = (
                "Te pregunto por cinco aspectos de tu perfil; vos elegís del 1 al 10 "
                "y un sistema de 25 reglas difusas arma tu mapa vocacional."
            )
        elif acto == "recuerdo":
            recuerdos = [
                contenido for rol, contenido in sesion.historial
                if rol == "user"
                and not contenido.startswith("Elegí ")
                and _valor_escrito(_normalizar(contenido)) is None
                and _acto_social(_normalizar(contenido)) is None
            ]
            hay_recuerdos = bool(recuerdos)
            respuesta = (
                f"Me contaste: «{recuerdos[-1]}»."
                if recuerdos else "Todavía no me contaste mucho sobre tus intereses."
            )
        elif acto == "despedida":
            respuesta = "¡Chau! Cuando quieras seguimos por acá."
        elif acto == "duda":
            respuesta = (
                "No hace falta estar seguro: elegí una aproximación del 1 al 10."
                if sesion.esperando_escala
                else "No pasa nada. Contame una primera impresión. " + pregunta
            )
        elif acto == "agradecimiento":
            respuesta = "¡De nada! Seguimos cuando quieras."
        else:
            raise ValueError(f"Acto social desconocido: {acto}")
        return self._turno(
            sesion,
            respuesta,
            generar=(
                acto in {"saludo", "estado", "agradecimiento", "despedida"}
                or acto == "recuerdo" and hay_recuerdos
            ),
            acto_social=acto,
        )

    def _turno(
        self, sesion: Sesion, respuesta: str, generar: bool = True,
        pregunta_respondida: str | None = None,
        acto_social: str | None = None,
    ) -> Turno:
        usado_llm = False
        if generar and self.generador is not None:
            pregunta = None
            if sesion.pregunta_actual is not None and not sesion.esperando_escala:
                candidata = _pregunta_vigente(sesion)
                if candidata in respuesta:
                    pregunta = candidata
            try:
                previos = sesion.mensajes_tema
                if previos and previos[-1] == sesion.mensaje_actual:
                    previos = previos[:-1]
                respuesta = self.generador.redactar(
                    mensaje=sesion.mensaje_actual,
                    respuesta_guia=respuesta,
                    hechos=sesion.hechos,
                    pregunta_pendiente=pregunta,
                    pregunta_respondida=pregunta_respondida,
                    dictamen=sesion.dictamen,
                    mensajes_previos=tuple(previos[-2:]),
                    historial=tuple(sesion.historial[-MAX_TURNOS_CONTEXTO:]),
                    acto_social=acto_social,
                    pregunta_generativa=(
                        pregunta is not None
                        and sesion.esperando_detalle
                        and sesion.explorando_alternativas == 0
                    ),
                    tema_actual=sesion.pregunta_actual,
                )
                usado_llm = True
            except Exception:  # noqa: BLE001 — respuesta guía si Ollama no está disponible
                pass
        if sesion.pregunta_actual is not None and not sesion.esperando_escala:
            preguntas = re.findall(r"¿[^?]+\?", respuesta)
            if preguntas:
                sesion.pregunta_mostrada = preguntas[-1]
        if sesion.mensaje_actual:
            sesion.historial.append(("user", sesion.mensaje_actual))
        sesion.historial.append(("assistant", respuesta))
        return Turno(
            respuesta=respuesta,
            sesion_id=sesion.id,
            hechos=dict(sesion.hechos),
            pendientes=_pendientes(sesion.hechos),
            dictamen=sesion.dictamen,
            usado_llm=usado_llm,
            escala_pendiente=(
                sesion.pregunta_actual if sesion.esperando_escala and sesion.dictamen is None else None
            ),
        )


def _pide_reinicio(mensaje: str) -> bool:
    return _normalizar(mensaje) in {"reiniciar", "reset", "de nuevo", "otra vez", "empezar"}
