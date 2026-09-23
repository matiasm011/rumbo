# Rumbo — chatbot de orientación vocacional (SED)

Sistema experto difuso de **25 reglas Mamdani**. El chat junta el perfil; Ollama (opcional) solo traduce texto a hechos 0–10. El dictamen no sale del LLM.

## Levantar

Hace falta Docker Desktop con integración WSL activada en esta distro.

```bash
docker compose up --build
```

La primera vez `ollama-init` baja `llama3.2:3b` (unos 2 GB). La app ya sirve en [http://localhost:8000](http://localhost:8000) aunque el pull no haya terminado: sin modelo, el NLU usa heurística y preguntas una a una.

## Sin Docker (dev)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Ollama local opcional en `http://127.0.0.1:11434`.

## Qué hay que defender

- Tema: orientación vocacional (STEM, salud, sociales, arte, negocios).
- Variables: analítico, social, creativo, ciencias de la vida, seguridad laboral.
- 25 reglas de producción en `backend/app/reglas.py`.
- Traza: cada respuesta lista las reglas disparadas y su grado.
- POST `/api/reglas` y POST `/api/inferir` para mostrar el motor sin chat.

`pytest` en `backend/` cubre el motor y el diálogo.
