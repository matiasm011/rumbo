from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud():
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["reglas"] >= 20


def test_listar_reglas():
    respuesta = cliente.get("/api/reglas")
    assert respuesta.json()["total"] == 25


def test_inferir_directo():
    respuesta = cliente.post(
        "/api/inferir",
        json={
            "analitico": 9,
            "social": 2,
            "creativo": 2,
            "ciencias_vida": 1,
            "seguridad_laboral": 6,
        },
    )
    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["area_principal"]["area"] == "stem"
    assert cuerpo["reglas_disparadas"]
