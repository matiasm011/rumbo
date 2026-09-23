from __future__ import annotations

from dataclasses import dataclass

ETIQUETAS = {
    "analitico": "analítico",
    "social": "social",
    "creativo": "creativo",
    "ciencias_vida": "ciencias de la vida",
    "seguridad_laboral": "seguridad laboral",
    "stem": "STEM",
    "salud": "salud",
    "sociales": "ciencias sociales",
    "arte": "arte y diseño",
    "negocios": "negocios",
}


@dataclass(frozen=True)
class Condicion:
    variable: str
    termino: str


@dataclass(frozen=True)
class ReglaProduccion:
    id: str
    condiciones: tuple[Condicion, ...]
    salida: str
    termino: str

    @property
    def enunciado(self) -> str:
        partes = [
            f"{ETIQUETAS[c.variable]} es {c.termino}" for c in self.condiciones
        ]
        si = " Y ".join(partes)
        return (
            f"SI {si} ENTONCES afinidad con {ETIQUETAS[self.salida]} "
            f"es {self.termino}"
        )


def _c(variable: str, termino: str) -> Condicion:
    return Condicion(variable, termino)


def _r(
    id_: str, condiciones: tuple[Condicion, ...], salida: str, termino: str
) -> ReglaProduccion:
    return ReglaProduccion(id_, condiciones, salida, termino)


# 25 reglas: 3 de cobertura por área + combinaciones que refinan el dictamen.
REGLAS: tuple[ReglaProduccion, ...] = (
    _r("R01", (_c("analitico", "bajo"),), "stem", "baja"),
    _r("R02", (_c("analitico", "medio"),), "stem", "media"),
    _r("R03", (_c("analitico", "alto"),), "stem", "alta"),
    _r("R04", (_c("ciencias_vida", "bajo"),), "salud", "baja"),
    _r("R05", (_c("ciencias_vida", "medio"),), "salud", "media"),
    _r("R06", (_c("ciencias_vida", "alto"),), "salud", "alta"),
    _r("R07", (_c("social", "bajo"),), "sociales", "baja"),
    _r("R08", (_c("social", "medio"),), "sociales", "media"),
    _r("R09", (_c("social", "alto"),), "sociales", "alta"),
    _r("R10", (_c("creativo", "bajo"),), "arte", "baja"),
    _r("R11", (_c("creativo", "medio"),), "arte", "media"),
    _r("R12", (_c("creativo", "alto"),), "arte", "alta"),
    _r("R13", (_c("seguridad_laboral", "bajo"),), "negocios", "baja"),
    _r("R14", (_c("seguridad_laboral", "medio"),), "negocios", "media"),
    _r("R15", (_c("seguridad_laboral", "alto"),), "negocios", "alta"),
    _r("R16", (_c("analitico", "alto"), _c("social", "bajo")), "stem", "alta"),
    _r("R17", (_c("analitico", "alto"), _c("creativo", "bajo")), "stem", "alta"),
    _r(
        "R18",
        (_c("ciencias_vida", "alto"), _c("social", "alto")),
        "salud",
        "alta",
    ),
    _r(
        "R19",
        (_c("ciencias_vida", "alto"), _c("analitico", "medio")),
        "salud",
        "alta",
    ),
    _r(
        "R20",
        (
            _c("social", "alto"),
            _c("analitico", "bajo"),
            _c("ciencias_vida", "bajo"),
        ),
        "sociales",
        "alta",
    ),
    _r(
        "R21",
        (_c("social", "alto"), _c("creativo", "medio")),
        "sociales",
        "alta",
    ),
    _r("R22", (_c("creativo", "alto"), _c("analitico", "bajo")), "arte", "alta"),
    _r(
        "R23",
        (_c("creativo", "alto"), _c("seguridad_laboral", "bajo")),
        "arte",
        "alta",
    ),
    _r(
        "R24",
        (
            _c("seguridad_laboral", "alto"),
            _c("analitico", "medio"),
            _c("social", "medio"),
        ),
        "negocios",
        "alta",
    ),
    _r(
        "R25",
        (
            _c("seguridad_laboral", "alto"),
            _c("ciencias_vida", "bajo"),
            _c("creativo", "bajo"),
        ),
        "negocios",
        "alta",
    ),
)
