from app.dominio import Perfil
from app.motor_difuso import inferir
from app.reglas import REGLAS


def test_hay_al_menos_20_reglas():
    assert len(REGLAS) >= 20
    ids = [regla.id for regla in REGLAS]
    assert len(ids) == len(set(ids))


def test_perfil_analitico_prioriza_stem():
    dictamen = inferir(
        Perfil(
            analitico=9.5,
            social=1.5,
            creativo=2.0,
            ciencias_vida=1.0,
            seguridad_laboral=6.0,
        )
    )
    assert dictamen.area_principal.area == "stem"
    assert dictamen.reglas_totales >= 20
    assert any(regla.id == "R16" for regla in dictamen.reglas_disparadas)


def test_perfil_salud_prioriza_salud():
    dictamen = inferir(
        Perfil(
            analitico=6.0,
            social=8.5,
            creativo=3.0,
            ciencias_vida=9.5,
            seguridad_laboral=7.0,
        )
    )
    assert dictamen.area_principal.area == "salud"
    assert any(regla.id == "R18" for regla in dictamen.reglas_disparadas)


def test_perfil_creativo_prioriza_arte():
    dictamen = inferir(
        Perfil(
            analitico=2.0,
            social=4.0,
            creativo=9.5,
            ciencias_vida=1.5,
            seguridad_laboral=2.0,
        )
    )
    assert dictamen.area_principal.area == "arte"


def test_todas_las_areas_tienen_afinidad():
    dictamen = inferir(
        Perfil(
            analitico=5,
            social=5,
            creativo=5,
            ciencias_vida=5,
            seguridad_laboral=5,
        )
    )
    assert {item.area for item in dictamen.afinidades} == {
        "stem",
        "salud",
        "sociales",
        "arte",
        "negocios",
    }
    assert dictamen.reglas_disparadas
