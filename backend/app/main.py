from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.dialogo import Dialogo
from app.dominio import AREAS, DESCRIPCION_AREA, Dictamen, Perfil
from app.generador import GeneradorRespuestas
from app.motor_difuso import inferir
from app.reglas import REGLAS

ESTATICOS = Path(__file__).resolve().parent.parent / "static"
dialogo = Dialogo(generador=GeneradorRespuestas())
app = FastAPI(title="Rumbo", version="1.0.0")


class ChatIn(BaseModel):
    mensaje: str = ""
    sesion_id: str | None = None
    valor: int | None = Field(default=None, ge=1, le=10)


class PerfilIn(BaseModel):
    analitico: float = Field(ge=0, le=10)
    social: float = Field(ge=0, le=10)
    creativo: float = Field(ge=0, le=10)
    ciencias_vida: float = Field(ge=0, le=10)
    seguridad_laboral: float = Field(ge=0, le=10)


@app.post("/api/sesion")
def abrir_sesion():
    return _turno_json(dialogo.iniciar())


@app.post("/api/chat")
def chat(cuerpo: ChatIn):
    turno = dialogo.responder(cuerpo.sesion_id, cuerpo.mensaje, cuerpo.valor)
    return _turno_json(turno)


@app.post("/api/inferir")
def inferir_directo(perfil: PerfilIn):
    dictamen = inferir(Perfil(**perfil.model_dump()))
    return _dictamen_json(dictamen)


@app.get("/api/reglas")
def listar_reglas():
    return {
        "total": len(REGLAS),
        "areas": list(AREAS),
        "reglas": [
            {"id": regla.id, "enunciado": regla.enunciado} for regla in REGLAS
        ],
    }


@app.get("/api/salud")
def salud():
    return {"ok": True, "reglas": len(REGLAS)}


@app.get("/")
def indice():
    return FileResponse(ESTATICOS / "index.html")


app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")


def _turno_json(turno) -> dict:
    return {
        "respuesta": turno.respuesta,
        "sesion_id": turno.sesion_id,
        "hechos": turno.hechos,
        "pendientes": list(turno.pendientes),
        "escala_pendiente": turno.escala_pendiente,
        "usado_llm": turno.usado_llm,
        "dictamen": _dictamen_json(turno.dictamen),
        "reglas_totales": turno.reglas_totales,
    }


def _dictamen_json(dictamen: Dictamen | None) -> dict | None:
    if dictamen is None:
        return None
    return {
        "resumen": dictamen.resumen,
        "area_principal": {
            "area": dictamen.area_principal.area,
            "etiqueta": dictamen.area_principal.etiqueta,
            "descripcion": DESCRIPCION_AREA[dictamen.area_principal.area],
            "valor": dictamen.area_principal.valor,
            "carreras": list(dictamen.area_principal.carreras),
        },
        "afinidades": [
            {
                "area": item.area,
                "etiqueta": item.etiqueta,
                "descripcion": DESCRIPCION_AREA[item.area],
                "valor": item.valor,
                "carreras": list(item.carreras),
            }
            for item in dictamen.afinidades
        ],
        "reglas_disparadas": [
            {
                "id": regla.id,
                "enunciado": regla.enunciado,
                "grado": regla.grado,
            }
            for regla in dictamen.reglas_disparadas
        ],
        "perfil": dictamen.perfil.as_dict(),
        "reglas_totales": dictamen.reglas_totales,
    }
