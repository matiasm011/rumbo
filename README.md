# Rumbo — chatbot de orientación vocacional (SED)

Sistema experto difuso de **25 reglas Mamdani**. Rumbo pregunta por cada tema y muestra una escala interactiva del 1 al 10 dentro del chat. Esos valores forman el perfil; Ollama (opcional) redacta respuestas breves. El dictamen lo calcula el sistema experto, no el LLM.

Rumbo conserva el intercambio de cada sesión por separado y envía a Ollama los últimos 6 mensajes del estudiante y del asistente como contexto (la memoria completa de la sesión se usa para armar la respuesta guía). Al abrir una conversación nueva o reiniciar, el contexto anterior no se comparte. La memoria vive en el proceso de la app y se pierde al reiniciarlo.
Ollama también puede redactar una repregunta a partir de lo que contó el estudiante. La app verifica que siga en el tema y conserva la pregunta guía si la propuesta no encaja; la escala aparece cuando corresponde en el flujo.

## Levantar (un solo comando)

Hace falta Docker Desktop con integración WSL activada en esta distro.

```bash
git clone https://github.com/matiasm011/rumbo.git
cd rumbo
docker compose up --build
```

Abrir [http://localhost:8000](http://localhost:8000).

La primera vez `ollama-init` baja `llama3.2:3b` (unos 2 GB, varios minutos según la conexión). No hace falta esperar: la app ya responde con textos guía, la escala del 1 al 10 sigue funcionando y el dictamen (sistema de 25 reglas) no depende del LLM. Cuando el modelo termina de bajar, las respuestas se vuelven generativas solas.

Sin GPU el LLM tarda unos segundos por turno en CPU; la guía instantánea aparece siempre al momento. Con NVIDIA en WSL, para respuestas de ~1s:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

## Sin Docker (dev)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Ollama local opcional en `http://127.0.0.1:11434`.

## Rendimiento del LLM

El prompt a Ollama está acotado para responder rápido en CPU: system breve,
últimos 6 turnos recortados a 200 caracteres, `num_ctx` 1024 y `num_predict`
40–60 según el turno. Ajustes por entorno: `OLLAMA_TIMEOUT` (20s),
`OLLAMA_MAX_TURNOS` (6), `OLLAMA_MAX_CHARS` (200), `OLLAMA_NUM_CTX` (1024),
`OLLAMA_KEEP_ALIVE` (30m).

## Sistema experto difuso

**Entradas:** 5 hechos crisp (0–10) que el estudiante confirma con la escala:
analítico, social, creativo, ciencias de la vida y seguridad laboral.
Cada uno se fuzzifica en tres términos: bajo, medio, alto, con triangulares
solapadas `bajo [0,0,5]`, `medio [2.5,5,7.5]`, `alto [5,10,10]`.

**Salidas:** afinidad (0–10) para 5 áreas — STEM, salud, ciencias sociales,
arte y diseño, negocios — con los mismos tres términos.

**Inferencia Mamdani** (`backend/app/motor_difuso.py`, con `scikit-fuzzy`):
AND del antecedente por mínimo, implicación por mínimo, agregación por máximo
y defuzzificación por centroide.

**25 reglas** (`backend/app/reglas.py`): R01–R15 dan cobertura total
(3 por área, una por término); R16–R25 combinan 2–3 condiciones para refinar
el dictamen (ej. *SI analítico es alto Y social es bajo ENTONCES afinidad
con STEM es alta*).

**Traza:** una regla dispara si su grado (mínimo de pertenencias del
antecedente) supera 0.01. El dictamen informa el área principal (afinidad
máxima), las 5 afinidades, las reglas disparadas con su grado y carreras
ilustrativas. Se ve en la UI ("Cómo se calculó este resultado") y por API:

```bash
curl http://localhost:8000/api/reglas            # lista las 25 reglas
curl -X POST http://localhost:8000/api/inferir \  # dictamen directo, sin chat
  -H 'Content-Type: application/json' \
  -d '{"analitico":9,"social":2,"creativo":2,"ciencias_vida":1,"seguridad_laboral":6}'
```

El LLM nunca decide: solo redacta respuestas breves a partir de una guía
determinística. Sin Ollama, el chat sigue funcionando y el dictamen es el mismo.

## Qué hay que defender

- Tema: orientación vocacional (STEM, salud, sociales, arte, negocios).
- Variables: analítico, social, creativo, ciencias de la vida, seguridad laboral.
- 25 reglas de producción en `backend/app/reglas.py`.
- Traza: cada respuesta lista las reglas disparadas y su grado.
- GET `/api/reglas` y POST `/api/inferir` para mostrar el motor sin chat.

`pytest` en `backend/` cubre el motor y el diálogo.
