import json

from fastapi.testclient import TestClient

from app.main import app
from app.dialogo import Dialogo
from app import main

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
    assert "Tecnología" in cuerpo["area_principal"]["descripcion"]
    assert cuerpo["reglas_disparadas"]


def test_chat_expone_escala_y_recibe_valor_interactivo(monkeypatch):
    monkeypatch.setattr(main, "dialogo", Dialogo())
    inicio = main.abrir_sesion()
    primero = main.chat(main.ChatIn(sesion_id=inicio["sesion_id"], mensaje="me gustan los números"))
    assert primero["escala_pendiente"] is None
    libre = main.chat(main.ChatIn(sesion_id=inicio["sesion_id"], mensaje="me gusta encontrar soluciones"))
    assert libre["escala_pendiente"] == "analitico"
    assert libre["hechos"] == {}

    puntuado = main.chat(main.ChatIn(sesion_id=inicio["sesion_id"], valor=8))
    assert puntuado["escala_pendiente"] is None
    assert puntuado["hechos"] == {"analitico": 8.0}
    assert puntuado["pendientes"][0] == "social"


def test_chat_stream_envia_guia_instantanea_y_final(monkeypatch):
    monkeypatch.setattr(main, "dialogo", Dialogo())
    inicio = cliente.post("/api/sesion").json()
    respuesta = cliente.post(
        "/api/chat/stream",
        json={"sesion_id": inicio["sesion_id"], "mensaje": "me gustan los números"},
    )
    assert respuesta.status_code == 200
    eventos = [
        json.loads(linea[5:].strip())
        for linea in respuesta.text.splitlines()
        if linea.startswith("data:")
    ]
    assert [evento["tipo"] for evento in eventos] == ["guia", "final"]
    assert eventos[0]["turno"]["respuesta"] == eventos[1]["turno"]["respuesta"]
    assert eventos[0]["turno"]["sesion_id"] == inicio["sesion_id"]
    assert "resolver un problema" in eventos[1]["turno"]["respuesta"]
