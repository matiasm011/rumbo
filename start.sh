#!/bin/sh
# Arranque para Hugging Face Spaces: Ollama y la app en un solo contenedor
# (los Spaces no tienen docker-compose ni sidecars).
set -u

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
PORT="${PORT:-7860}"

ollama serve > /tmp/ollama.log 2>&1 &

# Esperar al daemon (máx 60s) y bajar el modelo en segundo plano:
# la app arranca ya con textos guía y se vuelve generativa sola.
for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then break; fi
  sleep 1
done
ollama pull "$OLLAMA_MODEL" >> /tmp/ollama.log 2>&1 &

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
