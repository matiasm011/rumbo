from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.dominio import PREGUNTAS, VARIABLES, Dictamen, Perfil
from app.motor_difuso import inferir
from app.nlu import ExtractorHechos, Extraccion


SALUDO = (
    "Soy Rumbo, un chatbot de orientación vocacional. "
    "El dictamen lo hace un sistema experto difuso con 25 reglas de producción; "
    "yo solo te ayudo a completar el perfil. "
    "Contame cómo sos o respondé de a una pregunta. "
    "¿Arrancamos por lo analítico: matemáticas, lógica, sistemas?"
)


@dataclass
class Sesion:
    id: str
    hechos: dict[str, float] = field(default_factory=dict)
    dictamen: Dictamen | None = None
    usado_llm: bool = False


@dataclass(frozen=True)
class Turno:
    respuesta: str
    sesion_id: str
    hechos: dict[str, float]
    pendientes: tuple[str, ...]
    dictamen: Dictamen | None
    usado_llm: bool
    reglas_totales: int = 25


class Dialogo:
    def __init__(self, extractor: ExtractorHechos | None = None) -> None:
        self.extractor = extractor or ExtractorHechos()
        self._sesiones: dict[str, Sesion] = {}

    def iniciar(self) -> Turno:
        sesion = Sesion(id=str(uuid4()))
        self._sesiones[sesion.id] = sesion
        return self._turno(
            sesion,
            SALUDO,
            usado_llm=False,
        )

    def responder(self, sesion_id: str | None, mensaje: str) -> Turno:
        sesion = self._sesiones.get(sesion_id or "")
        if sesion is None:
            sesion = Sesion(id=str(uuid4()))
            self._sesiones[sesion.id] = sesion

        if sesion.dictamen is not None:
            if _pide_reinicio(mensaje):
                sesion.hechos.clear()
                sesion.dictamen = None
                sesion.usado_llm = False
                return self._turno(
                    sesion,
                    "Listo, perfil en blanco. " + PREGUNTAS[VARIABLES[0]],
                    usado_llm=False,
                )
            return self._turno(
                sesion,
                "Si querés otro dictamen, decime «reiniciar». "
                "El SED no vuelve a correr hasta tener un perfil nuevo.",
                usado_llm=False,
            )

        pendientes = _pendientes(sesion.hechos)
        pregunta = pendientes[0] if pendientes else None
        extraccion = self.extractor.extraer(mensaje, pendientes, pregunta)
        _aplicar(sesion, extraccion)
        pendientes = _pendientes(sesion.hechos)

        if not pendientes:
            perfil = Perfil.from_mapping(sesion.hechos)
            sesion.dictamen = inferir(perfil)
            texto = (
                f"{sesion.dictamen.resumen} "
                f"Abajo ves las {len(sesion.dictamen.reglas_disparadas)} reglas "
                f"que se dispararon (de {sesion.dictamen.reglas_totales})."
            )
            return self._turno(sesion, texto, usado_llm=sesion.usado_llm)

        faltan = ", ".join(pendientes)
        pregunta_txt = PREGUNTAS[pendientes[0]]
        if extraccion.hechos:
            texto = f"Anotado. Todavía falta: {faltan}. {pregunta_txt}"
        else:
            texto = pregunta_txt
        return self._turno(sesion, texto, usado_llm=sesion.usado_llm)

    def _turno(self, sesion: Sesion, respuesta: str, usado_llm: bool) -> Turno:
        return Turno(
            respuesta=respuesta,
            sesion_id=sesion.id,
            hechos=dict(sesion.hechos),
            pendientes=_pendientes(sesion.hechos),
            dictamen=sesion.dictamen,
            usado_llm=usado_llm,
        )


def _pendientes(hechos: dict[str, float]) -> tuple[str, ...]:
    return tuple(nombre for nombre in VARIABLES if nombre not in hechos)


def _aplicar(sesion: Sesion, extraccion: Extraccion) -> None:
    sesion.hechos.update(extraccion.hechos)
    sesion.usado_llm = sesion.usado_llm or extraccion.usado_llm


def _pide_reinicio(mensaje: str) -> bool:
    texto = mensaje.strip().lower()
    return texto in {"reiniciar", "reset", "de nuevo", "otra vez", "empezar"}
