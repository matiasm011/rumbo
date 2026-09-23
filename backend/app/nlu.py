from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import httpx

from app.dominio import VARIABLES

_PALABRAS_ALTO = (
    "mucho",
    "muchísimo",
    "altísimo",
    "alto",
    "me copa",
    "me encanta",
    "bastante",
    "totalmente",
)
_PALABRAS_MEDIO = (
    "más o menos",
    "mas o menos",
    "regular",
    "ni tanto",
    "depende",
)
_PALABRAS_BAJO = (
    "nada",
    "poco",
    "para nada",
    "no me va",
    "odio",
    "ni ahí",
    "bajo",
)

_CLAVES = {
    "analitico": (
        "mate",
        "número",
        "numero",
        "lógica",
        "logica",
        "program",
        "sistema",
        "ingenier",
        "física",
        "fisica",
        "cálculo",
        "calculo",
        "datos",
    ),
    "social": (
        "persona",
        "gente",
        "enseñ",
        "ayud",
        "cuidar",
        "psicolog",
        "hablar",
        "equipo",
        "derecho",
        "educa",
    ),
    "creativo": (
        "diseñ",
        "arte",
        "música",
        "musica",
        "crear",
        "dibuj",
        "audiovisual",
        "arquitect",
        "escribir",
        "creativ",
    ),
    "ciencias_vida": (
        "médic",
        "medic",
        "salud",
        "cuerpo",
        "biolog",
        "enferm",
        "kinesio",
        "nutri",
        "hospital",
        "vivo",
        "vida",
    ),
    "seguridad_laboral": (
        "laburo",
        "trabajo",
        "estable",
        "salida",
        "demanda",
        "sueldo",
        "plata",
        "inserción",
        "insercion",
        "empleo",
    ),
}


@dataclass(frozen=True)
class Extraccion:
    hechos: dict[str, float]
    usado_llm: bool
    error: str | None = None


class ExtractorHechos:
    def __init__(
        self,
        host: str | None = None,
        modelo: str | None = None,
        timeout: float = 45.0,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip(
            "/"
        )
        self.modelo = modelo or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout

    def extraer(
        self, mensaje: str, pendientes: tuple[str, ...], pregunta_actual: str | None
    ) -> Extraccion:
        heuristica = extraer_heuristico(mensaje, pendientes, pregunta_actual)
        try:
            llm = self._extraer_llm(mensaje, pendientes, pregunta_actual)
        except Exception as exc:  # noqa: BLE001 — fallback deliberado
            return Extraccion(hechos=heuristica, usado_llm=False, error=str(exc))

        hechos = {**heuristica, **llm}
        return Extraccion(hechos=hechos, usado_llm=True)

    def _extraer_llm(
        self, mensaje: str, pendientes: tuple[str, ...], pregunta_actual: str | None
    ) -> dict[str, float]:
        esquema = ", ".join(VARIABLES)
        prompt = f"""Sos el extractor de hechos de un sistema experto de orientación vocacional.
Devolvé SOLO un JSON con las claves que puedas inferir. Claves posibles: {esquema}.
Cada valor es un número de 0 a 10. Si no está claro, no incluyas esa clave.
Pendientes: {", ".join(pendientes) or "ninguna"}.
Pregunta que se le hizo al estudiante: {pregunta_actual or "ninguna"}.
Mensaje del estudiante: {mensaje}
"""
        with httpx.Client(timeout=self.timeout) as cliente:
            respuesta = cliente.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.modelo,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Respondé únicamente JSON válido.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            respuesta.raise_for_status()
            contenido = respuesta.json()["message"]["content"]
        return _parsear_hechos(contenido)


def extraer_heuristico(
    mensaje: str, pendientes: tuple[str, ...], pregunta_actual: str | None
) -> dict[str, float]:
    texto = mensaje.lower()
    hechos: dict[str, float] = {}
    numero = _primer_numero(texto)

    if pregunta_actual and numero is not None:
        hechos[pregunta_actual] = numero
    elif pregunta_actual and (nivel := _nivel_linguistico(texto)) is not None:
        hechos[pregunta_actual] = nivel

    for variable, claves in _CLAVES.items():
        if variable in hechos:
            continue
        if not any(clave in texto for clave in claves):
            continue
        if numero is not None and (not pendientes or variable in pendientes):
            hechos[variable] = numero
        elif (nivel := _nivel_linguistico(texto)) is not None:
            hechos[variable] = nivel
        elif pregunta_actual == variable:
            continue
        else:
            hechos[variable] = 7.5
    return hechos


def _parsear_hechos(contenido: str) -> dict[str, float]:
    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", contenido, re.DOTALL)
        if not match:
            return {}
        datos = json.loads(match.group(0))
    hechos: dict[str, float] = {}
    if not isinstance(datos, dict):
        return hechos
    for clave, valor in datos.items():
        if clave not in VARIABLES:
            continue
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            continue
        hechos[clave] = max(0.0, min(10.0, numero))
    return hechos


def _primer_numero(texto: str) -> float | None:
    match = re.search(r"\b(\d+(?:[.,]\d+)?)\b", texto)
    if not match:
        return None
    numero = float(match.group(1).replace(",", "."))
    if 0 <= numero <= 10:
        return numero
    return None


def _nivel_linguistico(texto: str) -> float | None:
    if any(palabra in texto for palabra in _PALABRAS_BAJO):
        return 2.0
    if any(palabra in texto for palabra in _PALABRAS_MEDIO):
        return 5.0
    if any(palabra in texto for palabra in _PALABRAS_ALTO):
        return 8.5
    if texto.strip() in {"sí", "si", "ok", "dale"}:
        return 8.0
    return None
