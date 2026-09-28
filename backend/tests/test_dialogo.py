import pytest

from app.dialogo import Dialogo
from app.nlu import ExtractorHechos, detectar_tema, extraer_heuristico


def test_heuristica_toma_numero_de_la_pregunta_actual():
    hechos = extraer_heuristico("diría un 8", ("analitico",), "analitico")
    assert hechos["analitico"] == 8.0


def test_heuristica_detecta_poco():
    hechos = extraer_heuristico("me interesa poco", ("creativo",), "creativo")
    assert hechos["creativo"] == 2.0


def test_respuesta_espontanea_no_se_atribuye_a_la_pregunta_anterior():
    hechos = extraer_heuristico(
        "me encanta dibujar", ("analitico", "creativo"), "analitico"
    )
    assert "analitico" not in hechos
    assert hechos["creativo"] > 7


@pytest.mark.parametrize(
    ("mensaje", "tema"),
    (
        ("No me gusta trabajar en grupo porque todos hablan", "social"),
        ("Me gusta dibujar personajes para videojuegos", "creativo"),
        ("La biología no me interesa mucho", "ciencias_vida"),
        ("Me divierten los acertijos, aunque matemáticas me cuesta", "analitico"),
        ("Quiero un empleo con estabilidad", "seguridad_laboral"),
    ),
)
def test_detecta_tema_sin_confundir_palabras_parecidas(mensaje, tema):
    from app.dominio import VARIABLES

    assert detectar_tema(mensaje, VARIABLES, "analitico") == tema


class ExtractorEspia(ExtractorHechos):
    def __init__(self):
        self.llamadas = []

    def _extraer_llm(self, mensaje, pendientes, pregunta_actual):
        self.llamadas.append(mensaje)
        return {}


def test_nlu_no_consulta_llm_ante_un_saludo():
    extractor = ExtractorEspia()
    pendientes = ("analitico", "social", "creativo", "ciencias_vida", "seguridad_laboral")
    for saludo in ("hola", "Hola!", "buenas", ""):
        extraccion = extractor.extraer(saludo, pendientes, None)
        assert extraccion.hechos == {}
        assert extraccion.usado_llm is False
    assert extractor.llamadas == []


def test_inicio_pregunta_de_forma_general_sin_mostrar_escala():
    inicio = Dialogo().iniciar()
    assert "cómo te llevás con los números" in inicio.respuesta
    assert inicio.escala_pendiente is None
    assert inicio.hechos == {}
    assert len(inicio.pendientes) == 5


def test_dialogo_repregunta_antes_de_mostrar_escala_sin_inventar_puntuacion():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    repregunta = dialogo.responder(inicio.sesion_id, "me gustan los números")
    assert repregunta.escala_pendiente is None
    assert "resolver un problema" in repregunta.respuesta
    assert repregunta.hechos == {}
    turno = dialogo.responder(inicio.sesion_id, "me gusta encontrar la solución")
    assert turno.escala_pendiente == "analitico"
    assert turno.hechos == {}
    assert len(turno.pendientes) == 5
    assert "escala" in turno.respuesta


def test_prefiere_otra_actividad_y_rumbo_pregunta_por_sus_intereses():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    turno = dialogo.responder(
        inicio.sesion_id, "me llevo bien, pero prefiero hacer algo no relacionado con ellos"
    )
    assert turno.escala_pendiente is None
    assert "¿Qué actividades o temas sí te interesan más?" in turno.respuesta
    assert "acertijo" not in turno.respuesta
    assert turno.hechos == {}


def test_interes_sin_categoria_sigue_la_charla_sin_mostrar_escala_analitica():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(
        inicio.sesion_id, "me llevo bien, pero prefiero hacer algo no relacionado con ellos"
    )
    cocinar = dialogo.responder(inicio.sesion_id, "me interesa cocinar")
    assert cocinar.escala_pendiente is None
    assert "¿Qué es lo que más te gusta de eso?" in cocinar.respuesta
    detalle = dialogo.responder(inicio.sesion_id, "inventar recetas")
    assert detalle.escala_pendiente is None
    assert "crear o imaginar" in detalle.respuesta
    assert detalle.hechos == {}


def test_saludo_con_error_de_escritura_no_muestra_escala():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    primero = dialogo.responder(inicio.sesion_id, "como andas")
    segundo = dialogo.responder(inicio.sesion_id, "como anfas")
    for turno in (primero, segundo):
        assert turno.escala_pendiente is None
        assert turno.hechos == {}
        assert turno.dictamen is None


def test_pregunta_social_no_salta_la_repregunta():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me interesan los acertijos")
    social = dialogo.responder(inicio.sesion_id, "como andas")
    assert social.escala_pendiente is None
    assert "Bien, gracias" in social.respuesta
    detalle = dialogo.responder(inicio.sesion_id, "me gusta probar distintas soluciones")
    assert detalle.escala_pendiente == "analitico"


def test_tocar_un_valor_registra_el_hecho_y_pregunta_por_el_siguiente_tema():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me encantan los números")
    dialogo.responder(inicio.sesion_id, "me gusta buscar la solución")
    turno = dialogo.responder(inicio.sesion_id, valor=8)
    assert turno.hechos == {"analitico": 8.0}
    assert turno.escala_pendiente is None
    assert turno.pendientes[0] == "social"
    assert "trabajar con otras personas" in turno.respuesta


def test_cada_tema_pasa_por_charla_y_escala_antes_del_resultado():
    dialogo = Dialogo()
    sesion = dialogo.iniciar()
    respuestas = (
        ("analitico", "me encantan los números", 9),
        ("social", "me gusta ayudar a otras personas", 2),
        ("creativo", "me gusta diseñar", 2),
        ("ciencias_vida", "la biología me interesa poco", 1),
        ("seguridad_laboral", "quiero estabilidad laboral", 6),
    )
    for posicion, (clave, mensaje, valor) in enumerate(respuestas, start=1):
        repregunta = dialogo.responder(sesion.sesion_id, mensaje)
        assert repregunta.escala_pendiente is None
        assert clave not in repregunta.hechos
        libre = dialogo.responder(sesion.sesion_id, "me interesa pensarlo un poco más")
        assert libre.escala_pendiente == clave
        puntuado = dialogo.responder(sesion.sesion_id, valor=valor)
        assert puntuado.hechos[clave] == valor
        assert len(puntuado.hechos) == posicion
        assert puntuado.escala_pendiente is None

    assert puntuado.dictamen is not None
    assert puntuado.dictamen.area_principal.area == "stem"
    assert puntuado.dictamen.reglas_totales >= 20


def test_respuesta_sobre_otro_tema_cambia_la_escala_sin_puntuar_analitico():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    repregunta = dialogo.responder(inicio.sesion_id, "me encanta dibujar")
    assert "crear o imaginar" in repregunta.respuesta
    libre = dialogo.responder(inicio.sesion_id, "me gusta dibujar personajes")
    assert libre.escala_pendiente == "creativo"
    puntuado = dialogo.responder(inicio.sesion_id, valor=8)
    assert puntuado.hechos == {"creativo": 8.0}
    assert puntuado.pendientes[0] == "analitico"
    assert "números" in puntuado.respuesta
    assert "Para empezar" not in puntuado.respuesta


def test_cambia_de_tema_durante_repregunta_sin_mostrar_escala_anterior():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    primera = dialogo.responder(inicio.sesion_id, "La biología no me interesa mucho")
    assert "biología" in primera.respuesta
    cambio = dialogo.responder(inicio.sesion_id, "Me atrae más hacer cosas con computadoras")
    assert cambio.escala_pendiente is None
    assert "resolver un problema" in cambio.respuesta
    detalle = dialogo.responder(inicio.sesion_id, "Me gusta resolver acertijos")
    assert detalle.escala_pendiente == "analitico"


@pytest.mark.parametrize(
    ("mensaje", "fragmento"),
    (
        ("No me gusta trabajar en grupo porque todos hablan", "alguien de a uno"),
        ("Me gusta dibujar personajes para videojuegos", "diseñar esos personajes"),
        ("La biología no me interesa mucho", "no te atrae de la biología"),
    ),
)
def test_repregunta_toma_un_detalle_del_estudiante(mensaje, fragmento):
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    turno = dialogo.responder(inicio.sesion_id, mensaje)
    assert fragmento in turno.respuesta
    assert turno.escala_pendiente is None


def test_pregunta_social_durante_la_escala_conserva_los_botones():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    dialogo.responder(inicio.sesion_id, "disfruto encontrar soluciones")
    social = dialogo.responder(inicio.sesion_id, "¿Qué sos?")
    assert "asistente de orientación vocacional" in social.respuesta
    assert social.escala_pendiente == "analitico"
    assert social.hechos == {}
    puntuado = dialogo.responder(inicio.sesion_id, valor=7)
    assert puntuado.hechos == {"analitico": 7.0}


def test_no_acepta_valor_antes_de_mostrar_escala_ni_fuera_de_rango():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    prematuro = dialogo.responder(inicio.sesion_id, valor=8)
    assert prematuro.hechos == {}
    assert prematuro.escala_pendiente is None
    assert "Primero contame" in prematuro.respuesta
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    aun_prematuro = dialogo.responder(inicio.sesion_id, valor=8)
    assert aun_prematuro.escala_pendiente is None
    assert aun_prematuro.hechos == {}
    assert "resolver un problema" in aun_prematuro.respuesta
    with pytest.raises(ValueError, match="entre 1 y 10"):
        dialogo.responder(inicio.sesion_id, valor=0)
    with pytest.raises(ValueError, match="entre 1 y 10"):
        dialogo.responder(inicio.sesion_id, valor=11)


def test_se_puede_escribir_el_numero_despues_de_mostrar_escala():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    dialogo.responder(inicio.sesion_id, "disfruto encontrar soluciones")
    turno = dialogo.responder(inicio.sesion_id, "8")
    assert turno.hechos == {"analitico": 8.0}
    assert turno.escala_pendiente is None


def test_reinicio_vuelve_a_la_primera_pregunta():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    for respuesta in (
        "me gustan los números", "me gusta ayudar a personas", "me gusta diseñar",
        "me interesa la biología", "quiero trabajo estable",
    ):
        dialogo.responder(inicio.sesion_id, respuesta)
        dialogo.responder(inicio.sesion_id, "me interesa explorar eso")
        turno = dialogo.responder(inicio.sesion_id, valor=5)
    assert turno.dictamen is not None
    reinicio = dialogo.responder(inicio.sesion_id, "reiniciar")
    assert reinicio.hechos == {}
    assert reinicio.dictamen is None
    assert reinicio.escala_pendiente is None
    assert "números" in reinicio.respuesta


def test_duda_no_cierra_ni_puntua_la_escala():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    dialogo.responder(inicio.sesion_id, "me gusta resolver acertijos")
    duda = dialogo.responder(inicio.sesion_id, "no sé")
    assert duda.hechos == {}
    assert duda.escala_pendiente == "analitico"
    assert "1 al 10" in duda.respuesta


def test_responder_guia_no_muta_la_sesion_y_anticipa_la_respuesta():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    guia = dialogo.responder_guia(inicio.sesion_id, "me gustan los números")
    assert guia.usado_llm is False
    assert guia.sesion_id == inicio.sesion_id
    assert guia.escala_pendiente is None
    # La guía no avanzó la sesión real: el turno real sigue el flujo normal.
    repregunta = dialogo.responder(inicio.sesion_id, "me gustan los números")
    assert repregunta.respuesta == guia.respuesta
    assert repregunta.escala_pendiente is None
    assert "resolver un problema" in repregunta.respuesta
    libre = dialogo.responder(inicio.sesion_id, "me gusta encontrar la solución")
    assert libre.escala_pendiente == "analitico"


def test_responder_guia_con_valor_no_registra_el_hecho():
    dialogo = Dialogo()
    inicio = dialogo.iniciar()
    dialogo.responder(inicio.sesion_id, "me gustan los números")
    dialogo.responder(inicio.sesion_id, "me gusta encontrar la solución")
    guia = dialogo.responder_guia(inicio.sesion_id, valor=8)
    assert guia.hechos == {}
    assert "Anotado: 8/10." in guia.respuesta
    puntuado = dialogo.responder(inicio.sesion_id, valor=8)
    assert puntuado.hechos == {"analitico": 8.0}
