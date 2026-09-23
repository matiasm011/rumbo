from app.dialogo import Dialogo
from app.nlu import ExtractorHechos, extraer_heuristico


class ExtractorFijo(ExtractorHechos):
    def __init__(self, hechos: dict[str, float]):
        self._hechos = hechos

    def extraer(self, mensaje, pendientes, pregunta_actual):
        from app.nlu import Extraccion

        return Extraccion(hechos=self._hechos, usado_llm=False)


def test_heuristica_toma_numero_de_la_pregunta_actual():
    hechos = extraer_heuristico("diría un 8", ("analitico",), "analitico")
    assert hechos["analitico"] == 8.0


def test_heuristica_detecta_poco():
    hechos = extraer_heuristico("me interesa poco", ("creativo",), "creativo")
    assert hechos["creativo"] == 2.0


def test_dialogo_completa_perfil_y_dictamina():
    dialogo = Dialogo(extractor=ExtractorFijo({}))
    inicio = dialogo.iniciar()
    assert inicio.dictamen is None

    dialogo_lleno = Dialogo(
        extractor=ExtractorFijo(
            {
                "analitico": 9,
                "social": 2,
                "creativo": 2,
                "ciencias_vida": 1,
                "seguridad_laboral": 6,
            }
        )
    )
    sesion = dialogo_lleno.iniciar()
    turno = dialogo_lleno.responder(sesion.sesion_id, "me gustan los números")
    assert turno.dictamen is not None
    assert turno.dictamen.area_principal.area == "stem"
    assert turno.dictamen.reglas_totales >= 20
