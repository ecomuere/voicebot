# Imagen para Bedrock AgentCore Runtime: linux/arm64, puerto 8080,
# WebSocket en /ws y health check en /ping.
# Build: docker buildx build --platform linux/arm64 -t <ecr-uri>:latest --push .
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV VOICEBOT_HOST=0.0.0.0 \
    VOICEBOT_PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["voicebot-server"]
