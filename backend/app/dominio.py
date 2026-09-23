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

CARRERAS = {
    "stem": ("Ingeniería", "Ciencias de datos", "Sistemas", "Ciencias exactas"),
    "salud": ("Medicina", "Enfermería", "Kinesiología", "Nutrición"),
    "sociales": ("Psicología", "Educación", "Derecho", "Trabajo social"),
    "arte": ("Diseño", "Arquitectura", "Artes", "Comunicación audiovisual"),
    "negocios": ("Administración", "Economía", "Marketing", "Contador público"),
}

PREGUNTAS = {
    "analitico": (
        "¿Qué tanto te llevan las matemáticas, la lógica o armar sistemas? "
        "Podés decir un número del 0 al 10 o contarlo con tus palabras."
    ),
    "social": (
        "¿Te ves trabajando con personas: enseñar, ayudar, negociar, acompañar? "
        "0 es casi nada, 10 es el centro de lo que querés hacer."
    ),
    "creativo": (
        "¿Cuánto pesa crear, diseñar o expresar ideas en tu día a día?"
    ),
    "ciencias_vida": (
        "¿Te interesa el cuerpo, la biología, la salud o entender cómo funciona lo vivo?"
    ),
    "seguridad_laboral": (
        "¿Qué tan importante es para vos una salida laboral estable y con demanda?"
    ),
}


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
