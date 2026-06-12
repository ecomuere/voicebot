# Voicebot — speech-to-speech con Strands Agents

Voicebot en Python construido con [Strands Agents](https://strandsagents.com) y
**Amazon Nova Sonic** (Bedrock) en modo *speech-to-speech* real: el audio entra
y sale del modelo en streaming bidireccional, sin pipeline STT → LLM → TTS.
Soporta interrupciones (*barge-in*) y herramientas (tool use) durante la llamada.

Se puede hablar con el bot por tres canales:

| Canal | Entrypoint | Cómo |
|---|---|---|
| 🌐 Navegador | `voicebot-server` | Cliente web en `/` (WebSocket + AudioWorklet) |
| ☎️ Teléfono | `voicebot-server` | Twilio Media Streams (`/twilio/voice` + `/ws/twilio`) |
| 🎙️ Micrófono local | `voicebot-local` | PyAudio en tu equipo |

## Arquitectura (hexagonal / ports & adapters)

```
src/voicebot/
├── domain/                  # Núcleo: sin dependencias externas
│   ├── audio.py             #   AudioFrame (VO), sample rates del dominio
│   ├── events.py            #   AgentSpoke, Interrupted, TranscriptReady...
│   └── ports.py             #   ConversationSession/Gateway, CallTransport, AudioTranscoder
├── application/
│   └── conversation.py      # Caso de uso: ConversationService.attend_call()
├── adapters/                # Implementaciones de los puertos
│   ├── strands_gateway.py   #   ConversationGateway → Strands BidiAgent + Nova Sonic
│   ├── strands_events.py    #   Eventos Strands → eventos de dominio (puro, testable)
│   ├── numpy_transcoder.py  #   AudioTranscoder → G.711 μ-law + remuestreo
│   ├── browser_transport.py #   CallTransport → WebSocket del navegador
│   ├── twilio_transport.py  #   CallTransport → Twilio Media Streams
│   └── tools.py             #   Herramientas del agente (hora, tiempo...)
├── entrypoints/
│   ├── http/app.py          # FastAPI: web + Twilio (driving adapters)
│   └── cli.py               # Modo micrófono local
├── bootstrap.py             # Composition root (único punto de cableado)
└── config.py                # Settings desde variables de entorno

infra/terraform/             # IaC: despliegue en Bedrock AgentCore Runtime
```

Principios aplicados:

- **Hexagonal**: `domain` y `application` no conocen Strands, Twilio, FastAPI ni numpy;
  dependen solo de puertos (`Protocol`). La dirección de dependencias siempre apunta
  hacia el dominio.
- **SOLID**: cada adaptador tiene una única responsabilidad; los casos de uso dependen
  de abstracciones (DIP); añadir un canal nuevo (p. ej. WebRTC o Amazon Connect) es un
  adaptador `CallTransport` más, sin tocar el dominio (OCP).
- **DDD**: lenguaje ubicuo en el modelo (`AudioFrame`, `AgentSpoke`, `Interrupted`,
  `TranscriptReady`); objetos de valor inmutables con invariantes validadas.

## Requisitos

- Python ≥ 3.12 (lo exige `BidiNovaSonicModel` de Strands)
- Credenciales AWS con acceso a Bedrock y al modelo `amazon.nova-sonic-v1:0`
  (disponible en `us-east-1`, `eu-north-1` y `ap-northeast-1`)
- Para el modo local: PortAudio (`brew install portaudio` / `apt install portaudio19-dev`)

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Configura AWS:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export VOICEBOT_REGION=us-east-1   # región de Bedrock con Nova Sonic
```

Variables opcionales: `VOICEBOT_VOICE` (voz de Nova Sonic, p. ej. `tiffany`),
`VOICEBOT_MODEL_ID`, `VOICEBOT_SYSTEM_PROMPT`, `VOICEBOT_HOST`, `VOICEBOT_PORT`.

## Uso

### 🌐 Llamar desde el navegador

```bash
voicebot-server
```

Abre <http://localhost:8000>, pulsa **Llamar** y habla. El cliente web captura el
micrófono (PCM16 a 16 kHz vía AudioWorklet), lo envía por WebSocket y reproduce la
voz del agente (PCM16 a 24 kHz). Las interrupciones vacían el buffer de reproducción
automáticamente. Nota: fuera de `localhost`, el navegador exige HTTPS para usar el micrófono.

### ☎️ Llamar por teléfono (Twilio)

1. Expón el servidor con una URL pública (por ejemplo `ngrok http 8000`).
2. En la consola de Twilio, configura el webhook de voz de tu número:
   `https://TU-DOMINIO/twilio/voice` (HTTP POST).
3. Llama a tu número de Twilio.

El webhook devuelve TwiML `<Connect><Stream>` apuntando a `wss://TU-DOMINIO/ws/twilio`;
el adaptador convierte el audio G.711 μ-law a 8 kHz de la red telefónica al PCM que
espera Nova Sonic (y viceversa), y envía `clear` a Twilio cuando el usuario interrumpe.

### 🎙️ Micrófono local

```bash
pip install -e ".[local]"   # añade PyAudio (requiere PortAudio del sistema)
voicebot-local
```

## Despliegue en AWS

> 📌 Decisión de arquitectura: el canal telefónico de producción usa **Amazon
> Connect nativo** con escalado a agente humano — ver
> [ADR 0001](docs/adr/0001-telefonia-con-amazon-connect-nativo.md).

La IaC (Terraform) está en [`infra/`](infra/README.md), organizada en stacks
independientes que pueden convivir:

- **EC2 + Twilio**: el contenedor en una instancia Graviton con TLS automático
  (Caddy). Cubre navegador y teléfono con nuestro agente Strands. La opción más
  directa para llamar por teléfono.
- **AgentCore Runtime**: navegador gestionado por AWS (WebSocket bidireccional
  con SigV4/Cognito). Twilio no puede firmar SigV4, así que el teléfono no se
  conecta directo a este stack.
- **Amazon Connect + Nova Sonic nativo**: teléfono sin servidores, pero la
  lógica conversacional se configura en Connect (no usa el código de este repo).

El contenedor (`Dockerfile`, linux/arm64, puerto 8080, `GET /ping`, WS en `/ws`)
cumple el contrato de AgentCore y es el mismo para EC2.

## Tests

```bash
pytest
```

Los tests son unitarios y no necesitan AWS, audio ni red: los puertos se sustituyen
por dobles (`tests/fakes.py`). Cubren el caso de uso de conversación, el códec
μ-law/remuestreo, los protocolos browser/Twilio y el mapeo de eventos de Strands.

## Extender

- **Herramientas de negocio** ([ADR 0002](docs/adr/0002-herramientas-de-negocio-compartidas-como-lambdas.md)):
  la regla de negocio vive una sola vez como Lambda en `lambdas/<capacidad>/`
  (ver `lambdas/order_status`), desplegada por `infra/terraform/tools` e
  invocada por ambos canales: el AI agent de Connect (teléfono) y una tool fina
  `@tool` en `adapters/tools.py` registrada en `strands_gateway.py` (web).
- **Herramientas locales simples**: funciones `@tool` directas en
  `adapters/tools.py` cuando no necesiten compartirse con Connect.
- **Nuevo canal** (WebRTC, Amazon Connect, Telegram...): implementa `CallTransport`
  y cablea el endpoint en `entrypoints/`.
- **Otro modelo speech-to-speech**: implementa `ConversationGateway` (Strands también
  trae modelos bidi de OpenAI Realtime y Gemini Live).
