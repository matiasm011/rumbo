FROM python:3.11-slim

WORKDIR /app

# Binario de Ollama: en HF Spaces no hay compose ni sidecars, el LLM corre
# en este mismo contenedor y la app se conecta por 127.0.0.1:11434.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates zstd \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSL https://ollama.com/download/ollama-linux-amd64.tar.zst \
  | zstd -d | tar -xf - -C /usr/local

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/static ./static
COPY start.sh .
RUN chmod +x start.sh

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    OLLAMA_HOST=http://127.0.0.1:11434 \
    OLLAMA_MODEL=llama3.2:3b \
    OLLAMA_KEEP_ALIVE=30m

EXPOSE 7860

CMD ["./start.sh"]
