# Canal telefónico: Amazon Connect + Nova Sonic con escalado a humano

> Opción elegida para el canal telefónico de producción — ver
> [ADR 0001](../../../docs/adr/0001-telefonia-con-amazon-connect-nativo.md).

La llamada comienza atendida por el **AI agent nativo de Connect** (Nova Sonic,
speech-to-speech, español soportado) y, cuando el llamante lo pide o el bot lo
decide, **escala a una cola de agentes humanos** con resumen automático de la
conversación. La lógica conversacional se configura en Connect, no en el
contenedor Strands de este repo (ese sirve el canal web).

## Qué crea Terraform

- Instancia de Connect (`CONNECT_MANAGED`) y número entrante (DID).
- **Horario de soporte** (`aws_connect_hours_of_operation`): L-V, franja
  configurable (`business_hours`, zona `time_zone`).
- **Cola `escalado-humano`** (`aws_connect_queue`): destino de la transferencia.
- **Routing profile `agentes-humanos`** vinculado a esa cola.
- Opcional: un **usuario agente** de ejemplo (softphone) si defines
  `agent_username` + `agent_password`.

```bash
terraform init
terraform apply \
  -var agent_username=agente1 \
  -var 'agent_password=CambiaEsto1!'   # opcional; omite ambos para no crear usuario
```

## Configuración en consola (no soportada aún por Terraform)

1. Entra en la consola de Connect (output `console_url`) y crea el usuario admin
   inicial.
2. Crea un **contact flow** de entrada con el bloque de conversación IA:
   - *Speech model* → **Speech-to-Speech** → proveedor **Amazon Nova Sonic**.
   - Activa **Enable AI Agent** y selecciona una voz compatible (hay voces en
     español).
3. Define el **AI agent** (instrucciones del sistema, acciones). Incluye en sus
   instrucciones cuándo debe escalar (p. ej. "si el cliente pide hablar con una
   persona o no puedes resolver su gestión, transfiere la llamada").
   - **Herramientas de negocio** ([ADR 0002](../../../docs/adr/0002-herramientas-de-negocio-compartidas-como-lambdas.md)):
     aplica el stack `../tools` con `connect_instance_arn` (output de este
     stack) para asociar las Lambdas compartidas a la instancia, y añade en el
     AI agent una acción que invoque `voicebot-order-status` con el parámetro
     `order_id`. Así el bot del teléfono y el del navegador responden igual.
4. Cablea el **escalado** en el flujo: a la salida de escalado del AI agent,
   añade `Set working queue` → cola **`escalado-humano`** (output
   `escalation_queue_name`) → `Transfer to queue`. Añade una rama para fuera de
   horario/cola llena (mensaje + colgar o buzón).
5. Asocia el número reclamado (output `phone_number`) al contact flow
   (*Channels → Phone numbers*).
6. Agentes humanos: asígnales el routing profile **`agentes-humanos`**; reciben
   las llamadas en el **Agent Workspace** con el resumen de la conversación del
   bot.
7. Llama al número y pide "quiero hablar con una persona" para probar el
   traspaso completo.

## Referencias

- [Use agentic self-service (Connect admin guide)](https://docs.aws.amazon.com/connect/latest/adminguide/agentic-self-service.html)
- [Configure Amazon Nova Sonic Speech-to-Speech (Connect admin guide)](https://docs.aws.amazon.com/connect/latest/adminguide/nova-sonic-speech-to-speech.html)
- [Amazon Connect agentic self-service (anuncio)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-connect-agentic-self-service/)
