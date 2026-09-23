from __future__ import annotations

from functools import lru_cache

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from app.dominio import (
    AREAS,
    CARRERAS,
    ETIQUETAS_AREA,
    VARIABLES,
    Afinidad,
    Dictamen,
    Perfil,
    ReglaDisparada,
)
from app.reglas import REGLAS, ReglaProduccion

UNIVERSO = np.arange(0, 10.01, 0.05)
TERMINOS_SALIDA = {"baja": "bajo", "media": "medio", "alta": "alto"}


def inferir(perfil: Perfil) -> Dictamen:
    simulacion = ctrl.ControlSystemSimulation(_sistema())
    valores = perfil.as_dict()
    for nombre, valor in valores.items():
        simulacion.input[nombre] = valor
    simulacion.compute()

    afinidades = tuple(
        Afinidad(
            area=area,
            etiqueta=ETIQUETAS_AREA[area],
            valor=round(float(simulacion.output[area]), 2),
            carreras=CARRERAS[area],
        )
        for area in AREAS
    )
    principal = max(afinidades, key=lambda item: item.valor)
    disparadas = _reglas_disparadas(valores)
    resumen = (
        f"El SED ubica tu perfil principalmente en {principal.etiqueta} "
        f"({principal.valor:.1f}/10). Carreras ilustrativas: "
        f"{', '.join(principal.carreras)}."
    )
    return Dictamen(
        afinidades=afinidades,
        area_principal=principal,
        reglas_disparadas=disparadas,
        perfil=perfil,
        resumen=resumen,
        reglas_totales=len(REGLAS),
    )


@lru_cache(maxsize=1)
def _antecedentes() -> dict[str, ctrl.Antecedent]:
    variables: dict[str, ctrl.Antecedent] = {}
    for nombre in VARIABLES:
        variable = ctrl.Antecedent(UNIVERSO, nombre)
        _membresia_triangular(variable)
        variables[nombre] = variable
    return variables


@lru_cache(maxsize=1)
def _consecuentes() -> dict[str, ctrl.Consequent]:
    salidas: dict[str, ctrl.Consequent] = {}
    for area in AREAS:
        variable = ctrl.Consequent(UNIVERSO, area)
        _membresia_triangular(variable)
        salidas[area] = variable
    return salidas


@lru_cache(maxsize=1)
def _sistema() -> ctrl.ControlSystem:
    antecedentes = _antecedentes()
    consecuentes = _consecuentes()
    reglas_sk = []
    for regla in REGLAS:
        antecedente = _antecedente_sk(regla, antecedentes)
        termino_sk = TERMINOS_SALIDA[regla.termino]
        consecuente = consecuentes[regla.salida][termino_sk]
        reglas_sk.append(ctrl.Rule(antecedente, consecuente, label=regla.id))
    return ctrl.ControlSystem(reglas_sk)


def _antecedente_sk(regla: ReglaProduccion, antecedentes: dict):
    acc = None
    for condicion in regla.condiciones:
        termino = antecedentes[condicion.variable][condicion.termino]
        acc = termino if acc is None else acc & termino
    return acc


def _membresia_triangular(variable: ctrl.Antecedent | ctrl.Consequent) -> None:
    variable["bajo"] = fuzz.trimf(variable.universe, [0, 0, 5])
    variable["medio"] = fuzz.trimf(variable.universe, [2.5, 5, 7.5])
    variable["alto"] = fuzz.trimf(variable.universe, [5, 10, 10])


def _pertenencia(variable: str, termino: str, valor: float) -> float:
    universo = UNIVERSO
    if termino == "bajo":
        mf = fuzz.trimf(universo, [0, 0, 5])
    elif termino == "medio":
        mf = fuzz.trimf(universo, [2.5, 5, 7.5])
    else:
        mf = fuzz.trimf(universo, [5, 10, 10])
    return float(fuzz.interp_membership(universo, mf, valor))


def _reglas_disparadas(valores: dict[str, float]) -> tuple[ReglaDisparada, ...]:
    disparadas: list[ReglaDisparada] = []
    for regla in REGLAS:
        grados = [
            _pertenencia(c.variable, c.termino, valores[c.variable])
            for c in regla.condiciones
        ]
        grado = min(grados) if grados else 0.0
        if grado > 0.01:
            disparadas.append(
                ReglaDisparada(
                    id=regla.id,
                    enunciado=regla.enunciado,
                    grado=round(grado, 3),
                )
            )
    disparadas.sort(key=lambda item: item.grado, reverse=True)
    return tuple(disparadas)
