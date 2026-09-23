# Orientación vocacional

Sistema experto difuso que dictamina afinidad hacia áreas vocacionales a partir del perfil de un estudiante. El chatbot solo adquiere hechos; el motor difuso decide.

## Language

**Perfil**:
Cinco hechos crisp (0 a 10) que describen al estudiante: analítico, social, creativo, ciencias de la vida y seguridad laboral.
_Avoid_: input, features, embedding

**Hecho**:
Valor numérico 0–10 de una variable del perfil, ya listo para fuzzificar. Puede faltar mientras el diálogo no lo cerró.
_Avoid_: slot, feature, score suelto

**Área vocacional**:
Una de cinco familias de carreras: STEM, Salud, Ciencias sociales, Arte y diseño, Negocios.
_Avoid_: carrera (una titulación concreta), profesión, output class

**Regla de producción**:
Implicación SI–ENTONCES sobre términos lingüísticos (bajo, medio, alto), no sobre números.
_Avoid_: prompt, heurística, if de código

**Dictamen**:
Resultado del SED: afinidad defuzzificada por área, área principal, reglas disparadas y carreras ilustrativas.
_Avoid_: predicción, respuesta del LLM, clasificación

**Regla disparada**:
Regla de producción cuyo grado de activación (mínimo de pertenencias del antecedente) es mayor que cero.
_Avoid_: token, atención, explicación del modelo

**NLU**:
Capa que traduce texto a hechos. No dictamina áreas.
_Avoid_: cerebro, motor, sistema experto
