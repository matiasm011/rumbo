# Rumbo — chatbot de orientación vocacional (SED)

Sistema experto difuso de **25 reglas Mamdani**. Rumbo pregunta por cada tema y muestra una escala interactiva del 1 al 10 dentro del chat. Esos valores forman el perfil; Ollama (opcional) redacta respuestas breves. El dictamen lo calcula el sistema experto, no el LLM.

Rumbo conserva el intercambio de cada sesión por separado y envía a Ollama los últimos 6 mensajes del estudiante y del asistente como contexto (la memoria completa de la sesión se usa para armar la respuesta guía). Al abrir una conversación nueva o reiniciar, el contexto anterior no se comparte. La memoria vive en el proceso de la app y se pierde al reiniciarlo.
Ollama también puede redactar una repregunta a partir de lo que contó el estudiante. La app verifica que siga en el tema y conserva la pregunta guía si la propuesta no encaja; la escala aparece cuando corresponde en el flujo.

## Levantar

Hace falta Docker Desktop con integración WSL activada en esta distro.

```bash
docker compose up --build
```

La primera vez `ollama-init` baja `llama3.2:3b` (unos 2 GB). La app ya sirve en [http://localhost:8000](http://localhost:8000) aunque el pull no haya terminado: sin modelo, el chat responde con textos guía y la escala sigue funcionando.

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

## Qué hay que defender

- Tema: orientación vocacional (STEM, salud, sociales, arte, negocios).
- Variables: analítico, social, creativo, ciencias de la vida, seguridad laboral.
- 25 reglas de producción en `backend/app/reglas.py`.
- Traza: cada respuesta lista las reglas disparadas y su grado.
- POST `/api/reglas` y POST `/api/inferir` para mostrar el motor sin chat.

`pytest` en `backend/` cubre el motor y el diálogo.
