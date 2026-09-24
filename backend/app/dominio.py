from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

VARIABLES = (
    "analitico",
    "social",
    "creativo",
    "ciencias_vida",
    "seguridad_laboral",
)

AREAS = (
    "stem",
    "salud",
    "sociales",
    "arte",
    "negocios",
)

ETIQUETAS_VARIABLE = {
    "analitico": "Analítico",
    "social": "Social",
    "creativo": "Creativo",
    "ciencias_vida": "Ciencias de la vida",
    "seguridad_laboral": "Seguridad laboral",
}

ETIQUETAS_AREA = {
    "stem": "STEM",
    "salud": "Salud",
    "sociales": "Ciencias sociales",
    "arte": "Arte y diseño",
    "negocios": "Negocios",
}

DESCRIPCION_AREA = {
    "stem": "Ciencia, Tecnología, Ingeniería y Matemática",
    "salud": "Medicina, cuidado y ciencias de la vida",
    "sociales": "Personas, educación, derecho y comunidad",
    "arte": "Diseño, expresión y comunicación",
    "negocios": "Gestión, economía y emprendimiento",
}

CARRERAS = {
    "stem": ("Ingeniería", "Ciencias de datos", "Sistemas", "Ciencias exactas"),
    "salud": ("Medicina", "Enfermería", "Kinesiología", "Nutrición"),
    "sociales": ("Psicología", "Educación", "Derecho", "Trabajo social"),
    "arte": ("Diseño", "Arquitectura", "Artes", "Comunicación audiovisual"),
    "negocios": ("Administración", "Economía", "Marketing", "Contador público"),
}

PREGUNTAS = {
    "analitico": (
        "Para empezar, ¿cómo te llevás con los números, los acertijos o resolver problemas?"
    ),
    "social": (
        "¿Y qué onda trabajar con otras personas, por ejemplo ayudando, enseñando o escuchando?"
    ),
    "creativo": (
        "¿Te gusta crear cosas, dibujar, diseñar o encontrar formas nuevas de expresar ideas?"
    ),
    "ciencias_vida": (
        "¿Te despierta curiosidad la biología, la salud o entender cómo funciona el cuerpo?"
    ),
    "seguridad_laboral": (
        "Y pensando en el futuro, ¿cuánto te importa que una carrera tenga trabajo estable?"
    ),
}

INDICACION_ESCALA = "Elegí del 1 al 10 en la escala de abajo."


@dataclass(frozen=True)
class Perfil:
    analitico: float
    social: float
    creativo: float
    ciencias_vida: float
    seguridad_laboral: float

    def as_dict(self) -> dict[str, float]:
        return {nombre: float(getattr(self, nombre)) for nombre in VARIABLES}

    @classmethod
    def from_mapping(cls, valores: Mapping[str, float]) -> Perfil:
        faltantes = [nombre for nombre in VARIABLES if nombre not in valores]
        if faltantes:
            raise ValueError(f"Perfil incompleto: {', '.join(faltantes)}")
        return cls(**{nombre: _acotar(valores[nombre]) for nombre in VARIABLES})


@dataclass(frozen=True)
class ReglaDisparada:
    id: str
    enunciado: str
    grado: float


@dataclass(frozen=True)
class Afinidad:
    area: str
    etiqueta: str
    valor: float
    carreras: tuple[str, ...]


@dataclass(frozen=True)
class Dictamen:
    afinidades: tuple[Afinidad, ...]
    area_principal: Afinidad
    reglas_disparadas: tuple[ReglaDisparada, ...]
    perfil: Perfil
    resumen: str
    reglas_totales: int = field(default=0)


def _acotar(valor: float) -> float:
    numero = float(valor)
    if numero < 0:
        return 0.0
    if numero > 10:
        return 10.0
    return numero
