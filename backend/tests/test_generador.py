import json

import httpx
import pytest

from app.dialogo import Dialogo
from app.dominio import INDICACION_ESCALA
from app.generador import GeneradorRespuestas


class GeneradorFijo:
    def __init__(self, respuesta: str):
        self.respuesta = respuesta
        self.llamadas = []

    def redactar(self, **contexto):
        self.llamadas.append(contexto)
        return self.respuesta


def test_dialogo_usa_respuesta_generada_sin_cambiar_el_perfil():
    generador = GeneradorFijo("Me encanta que me cuentes eso. Sigamos charlando.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    repregunta = dialogo.responder(inicio.sesion_id, "me gustan los números")
    libre = dialogo.responder(inicio.sesion_id, "me gusta resolver acertijos")
    turno = dialogo.responder(inicio.sesion_id, valor=9)

    assert "Soy Rumbo" in inicio.respuesta
    assert repregunta.escala_pendiente is None
    assert repregunta.usado_llm is True
    assert generador.llamadas[0]["mensaje"] == "me gustan los números"
    assert generador.llamadas[0]["pregunta_pendiente"] is not None
    assert generador.llamadas[0]["mensajes_previos"] == ()
    assert libre.escala_pendiente == "analitico"
    assert libre.usado_llm is True
    assert generador.llamadas[1]["mensajes_previos"] == ("me gustan los números",)
    assert turno.respuesta.startswith("Anotado: 9/10.")
    assert turno.hechos == {"analitico": 9.0}
    assert turno.escala_pendiente is None
    assert turno.usado_llm is False
    assert len(generador.llamadas) == 2


def test_cada_sesion_envia_solo_su_historial_al_generador():
    generador = GeneradorFijo("Te entiendo.")
    dialogo = Dialogo(generador=generador)
    uno = dialogo.iniciar()
    dos = dialogo.iniciar()

    dialogo.responder(uno.sesion_id, "me encanta dibujar")
    dialogo.responder(dos.sesion_id, "me gustan los números")
    dialogo.responder(uno.sesion_id, "invento personajes")

    assert generador.llamadas[0]["historial"] == (("assistant", uno.respuesta),)
    assert generador.llamadas[1]["historial"] == (("assistant", dos.respuesta),)
    assert generador.llamadas[2]["historial"][1:] == (
        ("user", "me encanta dibujar"),
        ("assistant", "Te entiendo."),
    )
    assert "me gustan los números" not in str(generador.llamadas[2]["historial"])


def test_saludo_social_usa_llm_sin_adelantar_la_escala():
    generador = GeneradorFijo("¡Bien, gracias! Acá estoy para charlar.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    primero = dialogo.responder(inicio.sesion_id, "como andas")
    segundo = dialogo.responder(inicio.sesion_id, "como andas")

    assert primero.usado_llm is True
    assert segundo.usado_llm is True
    assert segundo.escala_pendiente is None
    assert segundo.hechos == {}
    assert generador.llamadas[1]["historial"][-2:] == (
        ("user", "como andas"),
        ("assistant", primero.respuesta),
    )


def test_pregunta_por_lo_recordado_usa_el_historial_de_su_sesion():
    generador = GeneradorFijo("Me contaste que te gusta dibujar.")
    dialogo = Dialogo(generador=generador)
    uno = dialogo.iniciar()
    dos = dialogo.iniciar()
    dialogo.responder(uno.sesion_id, "me encanta dibujar")
    recuerdo = dialogo.responder(uno.sesion_id, "¿te acordás qué te dije?")
    dialogo.responder(dos.sesion_id, "¿te acordás qué te dije?")

    assert recuerdo.respuesta == "Me contaste que te gusta dibujar."
    assert recuerdo.escala_pendiente is None
    assert generador.llamadas[1]["acto_social"] == "recuerdo"
    assert ("user", "me encanta dibujar") in generador.llamadas[1]["historial"]
    assert len(generador.llamadas) == 2


def test_recuerdo_sin_ollama_no_mezcla_sesiones():
    class GeneradorCaido:
        def redactar(self, **contexto):
            raise httpx.ConnectError("Ollama no disponible")

    dialogo = Dialogo(generador=GeneradorCaido())
    uno = dialogo.iniciar()
    dos = dialogo.iniciar()
    dialogo.responder(uno.sesion_id, "me encanta dibujar")
    recuerdo_uno = dialogo.responder(uno.sesion_id, "¿te acordás qué te dije?")
    recuerdo_dos = dialogo.responder(dos.sesion_id, "¿te acordás qué te dije?")

    assert "me encanta dibujar" in recuerdo_uno.respuesta
    assert "dibujar" not in recuerdo_dos.respuesta
    assert recuerdo_dos.escala_pendiente is None


def test_saludo_generativo_conserva_reaccion_sin_pregunta_desalineada(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Estoy bien, gracias. ¿De qué te gustaría charlar?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    turno = dialogo.responder(inicio.sesion_id, "como andas")
    assert turno.respuesta == "Estoy bien, gracias."
    assert turno.escala_pendiente is None
    assert turno.hechos == {}
    assert turno.usado_llm is True


def test_recuerdo_descarta_primera_persona_incorrecta(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Me acordás que me dijiste que me encanta dibujar."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me encanta dibujar")
    recuerdo = dialogo.responder(inicio.sesion_id, "¿te acordás qué te dije?")
    assert recuerdo.respuesta == "Me contaste: «me encanta dibujar»."
    assert recuerdo.usado_llm is False


def test_estado_vuelve_a_respuesta_guia_si_modelo_no_contesta(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Estoy aquí para ayudarte a explorar carreras."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    turno = dialogo.responder(inicio.sesion_id, "como andas")
    assert "Bien, gracias" in turno.respuesta
    assert turno.escala_pendiente is None
    assert turno.usado_llm is False


def test_reiniciar_descarta_el_historial_de_la_conversacion_anterior():
    generador = GeneradorFijo("Te entiendo.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    for mensaje in (
        "me gustan los números", "me gusta ayudar a personas", "me gusta diseñar",
        "me interesa la biología", "quiero trabajo estable",
    ):
        dialogo.responder(inicio.sesion_id, mensaje)
        dialogo.responder(inicio.sesion_id, "me interesa explorar eso")
        dialogo.responder(inicio.sesion_id, valor=5)

    dialogo.responder(inicio.sesion_id, "reiniciar")
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    historial = generador.llamadas[-1]["historial"]
    assert historial[0] == ("user", "reiniciar")
    assert not any("biología" in contenido for _, contenido in historial)


def test_reiniciar_antes_del_resultado_tambien_borra_la_memoria():
    generador = GeneradorFijo("Te entiendo.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me encanta dibujar")
    reinicio = dialogo.responder(inicio.sesion_id, "reiniciar")
    dialogo.responder(inicio.sesion_id, "me gustan los números")

    assert "números" in reinicio.respuesta
    assert generador.llamadas[-1]["historial"] == (
        ("user", "reiniciar"),
        ("assistant", reinicio.respuesta),
    )


def test_contexto_enviado_al_llm_tiene_limite_por_sesion():
    generador = GeneradorFijo("¡Bien, gracias!")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    for _ in range(15):
        dialogo.responder(inicio.sesion_id, "como andas")
    historial = generador.llamadas[-1]["historial"]
    assert len(historial) == 24
    assert historial[-2:] == (("user", "como andas"), ("assistant", "¡Bien, gracias!"))


def test_dialogo_conserva_respuesta_guia_si_falla_generacion():
    class GeneradorCaido:
        def redactar(self, **contexto):
            raise httpx.ConnectError("Ollama no disponible")

    dialogo = Dialogo(generador=GeneradorCaido())
    inicio = dialogo.iniciar()
    turno = dialogo.responder(inicio.sesion_id, "¿Qué sos?")

    assert "Soy Rumbo" in inicio.respuesta
    assert "asistente de orientación vocacional" in turno.respuesta
    assert turno.hechos == {}
    assert turno.usado_llm is False


def test_preguntas_sobre_rumbo_conservan_datos_fijos_y_estado_es_generativo():
    generador = GeneradorFijo("¡Bien, gracias! Acá estoy para charlar.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    estado = dialogo.responder(inicio.sesion_id, "como andas")
    identidad = dialogo.responder(inicio.sesion_id, "que sos")
    funcionamiento = dialogo.responder(inicio.sesion_id, "como funcionas")
    assert "Bien, gracias" in estado.respuesta
    assert "Soy Rumbo" in identidad.respuesta
    assert "25 reglas" in funcionamiento.respuesta
    assert len(generador.llamadas) == 1
    assert generador.llamadas[0]["acto_social"] == "estado"


def test_generador_envia_contexto_vocacional_a_ollama(monkeypatch):
    peticiones = []

    def responder(peticion):
        peticiones.append(json.loads(peticion.content))
        return httpx.Response(
            200,
            json={"message": {"content": "¡Hola! Contame qué te gusta hacer."}},
        )

    cliente_real = httpx.Client
    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=transporte, timeout=timeout),
    )

    texto = GeneradorRespuestas().redactar(
        mensaje="hola",
        respuesta_guia="¡Hola! ¿Qué cosas te gustan?",
        hechos={},
        pregunta_pendiente=None,
        dictamen=None,
    )

    assert texto.startswith("¡Hola!")
    assert peticiones[0]["stream"] is False
    assert peticiones[0]["messages"][0]["role"] == "system"
    assert "25 reglas" in peticiones[0]["messages"][0]["content"]
    contexto = json.loads(peticiones[0]["messages"][1]["content"])
    assert contexto["mensaje_del_estudiante"] == "hola"
    assert contexto["resultado"] is None


def test_generador_mantiene_pregunta_del_perfil(monkeypatch):
    contexto_enviado = []

    def responder(peticion):
        cuerpo = json.loads(peticion.content)
        contexto_enviado.append(cuerpo["messages"][1]["content"])
        return httpx.Response(200, json={"message": {"content": "Te sigo."}})

    cliente_real = httpx.Client
    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=transporte, timeout=timeout),
    )

    pregunta = "¿Cómo te llevás con los números?"
    texto = GeneradorRespuestas().redactar(
        mensaje="me encanta dibujar",
        respuesta_guia=f"Entiendo. {pregunta}",
        hechos={"creativo": 8.5},
        pregunta_pendiente=pregunta,
        dictamen=None,
    )
    assert texto.endswith(pregunta)
    assert "Ahora dijo: me encanta dibujar" in contexto_enviado[0]
    assert f"Pregunta activa de Rumbo: {pregunta}" in contexto_enviado[0]


def test_modelo_puede_hacer_repregunta_concreta_del_mismo_tema(monkeypatch):
    peticiones = []

    def responder(peticion):
        peticiones.append(json.loads(peticion.content))
        return httpx.Response(200, json={"message": {"content": (
            "Te gusta dibujar personajes. ¿Qué historias te gusta inventarles?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="me gusta dibujar personajes",
        respuesta_guia="Te escucho. ¿Qué cosas te gusta crear o imaginar?",
        hechos={}, pregunta_pendiente="¿Qué cosas te gusta crear o imaginar?",
        dictamen=None, pregunta_generativa=True, tema_actual="creativo",
    )
    assert texto == "Te gusta dibujar personajes. ¿Qué historias te gusta inventarles?"
    assert "Tema para la repregunta: creativo" in peticiones[0]["messages"][-1]["content"]
    assert "¿Qué cosas te gusta crear o imaginar?" not in peticiones[0]["messages"][-1]["content"]


def test_repregunta_fuera_de_tema_se_reemplaza_por_la_guia(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Te gusta dibujar. ¿Te gustaría trabajar con otras personas?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="me gusta dibujar",
        respuesta_guia="Te escucho. ¿Qué cosas te gusta crear o imaginar?",
        hechos={}, pregunta_pendiente="¿Qué cosas te gusta crear o imaginar?",
        dictamen=None, pregunta_generativa=True, tema_actual="creativo",
    )
    assert texto == "Te gusta dibujar. ¿Qué cosas te gusta crear o imaginar?"


def test_repregunta_del_modelo_no_adelanta_la_escala(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Te gusta dibujar personajes. ¿Del 1 al 10 cuánto te gusta crear?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="me gusta dibujar personajes",
        respuesta_guia="Te escucho. ¿Qué cosas te gusta crear o imaginar?",
        hechos={}, pregunta_pendiente="¿Qué cosas te gusta crear o imaginar?",
        dictamen=None, pregunta_generativa=True, tema_actual="creativo",
    )
    assert texto == "Te gusta dibujar personajes. ¿Qué cosas te gusta crear o imaginar?"


def test_dialogo_recuerda_la_pregunta_generada_para_interpretar_la_respuesta():
    generador = GeneradorFijo(
        "Te gusta dibujar personajes. ¿Qué historias les inventás a tus personajes?"
    )
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    primera = dialogo.responder(inicio.sesion_id, "me gusta dibujar personajes")
    segunda = dialogo.responder(inicio.sesion_id, "les invento aventuras")

    assert "¿Qué historias les inventás a tus personajes?" in primera.respuesta
    assert generador.llamadas[1]["pregunta_respondida"] == (
        "¿Qué historias les inventás a tus personajes?"
    )
    assert segunda.escala_pendiente == "creativo"


def test_generador_envia_turnos_previos_con_roles_a_ollama(monkeypatch):
    peticiones = []

    def responder(peticion):
        peticiones.append(json.loads(peticion.content))
        return httpx.Response(200, json={"message": {"content": "Te gusta imaginar personajes."}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    GeneradorRespuestas().redactar(
        mensaje="me gusta inventar personajes",
        respuesta_guia="Te escucho. ¿Qué cosas te gusta crear o imaginar?",
        hechos={},
        pregunta_pendiente="¿Qué cosas te gusta crear o imaginar?",
        dictamen=None,
        historial=(
            ("assistant", "¿Qué te gusta hacer?"),
            ("user", "me encanta dibujar"),
            ("assistant", "Te gusta dibujar. ¿Qué cosas imaginás?"),
        ),
    )
    mensajes = peticiones[0]["messages"]
    assert [(item["role"], item["content"]) for item in mensajes[1:4]] == [
        ("assistant", "¿Qué te gusta hacer?"),
        ("user", "me encanta dibujar"),
        ("assistant", "Te gusta dibujar. ¿Qué cosas imaginás?"),
    ]
    assert mensajes[-1]["role"] == "user"
    assert "Ahora dijo: me gusta inventar personajes" in mensajes[-1]["content"]


def test_dialogo_da_al_modelo_la_pregunta_que_contestaba_el_estudiante():
    generador = GeneradorFijo("Te llevás bien con los números, aunque preferís otras actividades.")
    dialogo = Dialogo(generador=generador)
    inicio = dialogo.iniciar()
    dialogo.responder(
        inicio.sesion_id, "me llevo bien, pero prefiero hacer algo no relacionado con ellos"
    )
    assert "números" in generador.llamadas[0]["pregunta_respondida"]


def test_dialogo_descarta_reaccion_que_cambia_numeros_por_personas(monkeypatch):
    def responder(peticion):
        return httpx.Response(
            200,
            json={"message": {"content": "Te llevás bien con muchas personas."}},
        )

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    fuera_de_tema = dialogo.responder(inicio.sesion_id, "me gustan los números")
    assert "personas" not in fuera_de_tema.respuesta
    assert "problema o acertijo" in fuera_de_tema.respuesta
    assert fuera_de_tema.usado_llm is False

    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    turno = dialogo.responder(
        inicio.sesion_id, "y me llevo bien pero prefiero no hacer algo con eso"
    )

    assert "personas" not in turno.respuesta
    assert "te llevás bien con los números" in turno.respuesta
    assert "preferís no dedicarte" in turno.respuesta
    assert "Qué actividades o temas sí te interesan" in turno.respuesta
    assert turno.usado_llm is False


def test_dialogo_descarta_grupo_inventado_y_conserva_reaccion_contextual(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Te llevás bien con ellos, pero preferís trabajar en proyectos "
            "que no están relacionados con tu grupo."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    turno = dialogo.responder(
        inicio.sesion_id, "me llevo bien, pero prefiero hacer algo no relacionado con ellos"
    )
    assert "números" in turno.respuesta
    assert "preferís dedicarte a otras cosas" in turno.respuesta
    assert "grupo" not in turno.respuesta
    assert "¿Qué actividades o temas sí te interesan más?" in turno.respuesta
    assert turno.usado_llm is False


def test_dialogo_no_atribuye_al_bot_el_interes_del_estudiante(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Te interesa cocinar porque me gusta experimentar con diferentes sabores."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(
            transport=httpx.MockTransport(responder), timeout=timeout
        ),
    )
    dialogo = Dialogo(generador=GeneradorRespuestas())
    inicio = dialogo.iniciar()
    dialogo.responder(
        inicio.sesion_id, "me llevo bien, pero prefiero hacer algo no relacionado con ellos"
    )
    turno = dialogo.responder(inicio.sesion_id, "me interesa cocinar")
    assert turno.respuesta == "¿Qué es lo que más te gusta de eso?"
    assert turno.escala_pendiente is None
    assert turno.usado_llm is False


def test_generador_conserva_reaccion_y_reemplaza_pregunta_improvisada(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Entiendo que los números te cuestan, pero te divierten los acertijos, "
            "¿Querés hablar de carreras?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    pregunta = "¿Qué te suele pasar cuando tenés que resolver un problema o acertijo?"
    texto = GeneradorRespuestas().redactar(
        mensaje="Los números me cuestan, pero me divierten los acertijos",
        respuesta_guia=f"Te escucho. {pregunta}",
        hechos={}, pregunta_pendiente=pregunta, dictamen=None,
    )
    assert texto.startswith("Entiendo que los números te cuestan")
    assert texto.endswith(pregunta)
    assert "acertijos. ¿" in texto
    assert "carreras" not in texto


def test_generador_no_improvisa_pregunta_al_mostrar_escala(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Tiene sentido que pruebes varias ideas. ¿Qué te gusta más de eso?"
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="Me gusta probar varias ideas",
        respuesta_guia="Ahora lo entiendo un poco mejor. " + INDICACION_ESCALA,
        hechos={}, pregunta_pendiente=None, dictamen=None,
    )
    assert texto == "Tiene sentido que pruebes varias ideas. " + INDICACION_ESCALA


def test_generador_no_copia_primera_persona_del_estudiante(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Me gusta probar varias ideas hasta encontrar la solución."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="Me gusta probar varias ideas hasta encontrar la solución",
        respuesta_guia="Ahora lo entiendo un poco mejor. " + INDICACION_ESCALA,
        hechos={}, pregunta_pendiente=None, dictamen=None,
    )
    assert texto.startswith("Te gusta probar varias ideas")


def test_generador_usa_voseo_en_respuesta_social(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Prefieres escuchar a una persona y ayudarla."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="Prefiero escuchar a una persona y ayudarla",
        respuesta_guia="Ahora lo entiendo un poco mejor. " + INDICACION_ESCALA,
        hechos={}, pregunta_pendiente=None, dictamen=None,
    )
    assert texto.startswith("Preferís escuchar a una persona")


def test_generador_no_convierte_desinteres_en_interes(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "La biología no te llama la atención, aunque te parece interesante."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    pregunta = "¿Qué es lo que no te atrae de la biología o la salud?"
    texto = GeneradorRespuestas().redactar(
        mensaje="La biología no me interesa mucho",
        respuesta_guia="Te escucho. " + pregunta,
        hechos={}, pregunta_pendiente=pregunta, dictamen=None,
    )
    assert texto == "La biología no te llama la atención. " + pregunta


def test_generador_recorta_valoracion_no_mencionada(monkeypatch):
    def responder(peticion):
        return httpx.Response(200, json={"message": {"content": (
            "Preferís ayudar a una persona, es una forma muy valiosa de colaborar."
        )}})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    texto = GeneradorRespuestas().redactar(
        mensaje="Prefiero ayudar a una persona",
        respuesta_guia="Ahora lo entiendo un poco mejor. " + INDICACION_ESCALA,
        hechos={}, pregunta_pendiente=None, dictamen=None,
    )
    assert texto == "Preferís ayudar a una persona. " + INDICACION_ESCALA


def test_generador_rechaza_respuesta_que_confunde_a_rumbo_con_el_estudiante(monkeypatch):
    def responder(peticion):
        return httpx.Response(
            200,
            json={"message": {"content": "Che, sos Rumbo. Te ayudo a explorar carreras."}},
        )

    cliente_real = httpx.Client
    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=transporte, timeout=timeout),
    )

    with pytest.raises(ValueError, match="confundió quién es Rumbo"):
        GeneradorRespuestas().redactar(
            mensaje="¿Qué sos?",
            respuesta_guia="Soy Rumbo, un asistente virtual de orientación vocacional.",
            hechos={},
            pregunta_pendiente=None,
            dictamen=None,
        )


def test_generador_rechaza_preguntas_de_relleno(monkeypatch):
    def responder(peticion):
        return httpx.Response(
            200,
            json={"message": {"content": "¿Qué te gusta? ¿Qué te interesa? ¿Qué te motiva?"}},
        )

    cliente_real = httpx.Client
    transporte = httpx.MockTransport(responder)
    monkeypatch.setattr(
        "app.generador.httpx.Client",
        lambda timeout: cliente_real(transport=transporte, timeout=timeout),
    )

    with pytest.raises(ValueError, match="demasiado larga"):
        GeneradorRespuestas().redactar(
            mensaje="¿Cómo funcionás?",
            respuesta_guia="Te pregunto por cinco aspectos de tu perfil, del 1 al 10. "
            "Un sistema de 25 reglas difusas arma tu mapa vocacional.",
            hechos={},
            pregunta_pendiente=None,
            dictamen=None,
        )
