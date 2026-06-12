# ADR 0001 — Canal telefónico con Amazon Connect nativo y escalado a agente humano

- **Estado**: Aceptada
- **Fecha**: 2026-06-12
- **Decisores**: Iván Llorente

## Contexto

El voicebot es un agente speech-to-speech (Amazon Nova Sonic vía Strands Agents)
con dos canales previstos: navegador y teléfono. Surge un requisito nuevo para el
canal telefónico: **la llamada debe comenzar atendida por el bot y poder
transferirse a un agente humano** cuando el llamante lo pida o el bot lo decida.

Restricciones y hechos relevantes:

- El traspaso a humano necesita capacidades de contact center: colas, horarios,
  enrutamiento, y idealmente contexto/resumen de la conversación para el humano.
- Nuestro agente Strands corre como contenedor (EC2 o Bedrock AgentCore Runtime).
  AgentCore exige SigV4/JWT en su WebSocket, por lo que Twilio Media Streams no
  puede conectarse directamente.
- Desde re:Invent 2025, Amazon Connect integra **Nova Sonic de forma nativa** en
  sus contact flows ("agentic self-service"): el bloque de AI agent atiende la
  llamada en speech-to-speech y puede escalar a una cola humana con resumen
  automático de la conversación. Disponible en `us-east-1` y `us-west-2`;
  español soportado.
- Integrar nuestro contenedor Strands dentro de una llamada de Connect requeriría
  un adaptador de media streaming (Kinesis Video Streams) que no existe en el
  repo y es la integración de mayor complejidad.

## Opciones consideradas

1. **Connect nativo end-to-end**: el AI agent de Connect (Nova Sonic) atiende;
   el escalado es parte del contact flow (`Set working queue` →
   `Transfer to queue`), con resumen para el humano, grabación, Contact Lens y
   métricas incluidas. La lógica conversacional del canal telefónico se configura
   en Connect, no en este repo.
2. **Voicebot propio (Twilio) + transferencia a Connect**: herramienta
   `transfer_to_human` que redirige la llamada vía API REST de Twilio al número
   de Connect. Mantiene nuestro agente, pero el traspaso de contexto es artesanal
   (DynamoDB + Lambda) y se pagan dos plataformas por llamada transferida.
3. **Voicebot propio (Twilio) + transferencia a teléfonos directos**: igual que
   la 2 pero sin Connect; válida solo para equipos humanos muy pequeños y sin
   necesidades de cola/métricas.
4. **Agente Strands dentro de Connect (KVS)**: nuestro bot y los humanos en la
   misma llamada de Connect. Máxima coherencia, máxima complejidad; el adaptador
   no existe.

## Decisión

Adoptamos la **opción 1**: el canal telefónico se implementa con **Amazon
Connect y su integración nativa de Nova Sonic**, y el escalado a humano se
resuelve dentro del contact flow de Connect (AI agent → cola → agente humano en
el Agent Workspace, con resumen automático de la conversación).

Reparto de responsabilidades resultante:

- **Teléfono**: Connect (AI agent nativo + colas humanas). Infra base en
  `infra/terraform/connect`; el contact flow y el AI agent se configuran en la
  consola de Connect mientras Terraform no los soporte.
- **Navegador**: sigue siendo el agente Strands de este repo (self-hosted en EC2
  o en AgentCore Runtime).
- **Lógica de negocio compartida**: las capacidades que deban estar en ambos
  canales (consultas, reservas, CRM...) se exponen como APIs/Lambdas invocables
  tanto por el AI agent de Connect como por las tools de Strands
  (`adapters/tools.py`), para no duplicar reglas de negocio.

## Consecuencias

### Positivas

- Escalado a humano de primera clase: colas, horarios, enrutamiento, resumen
  automático al agente, grabación, Contact Lens y métricas sin desarrollo propio.
- Sin servidores que operar para el canal telefónico; número incluido en Connect.
- Sin puente SigV4 ni dependencia de Twilio para este canal.

### Negativas

- La lógica conversacional telefónica vive en Connect (consola), no en el repo:
  dos "cerebros" que mantener alineados (prompt del AI agent de Connect y
  `config.py` de Strands). Mitigación: negocio compartido vía APIs/Lambdas.
- Parte de la configuración (contact flow, AI agent) no es IaC todavía; queda
  documentada como runbook en `infra/terraform/connect/README.md`.
- Regiones limitadas (`us-east-1`/`us-west-2`) para Nova Sonic en Connect.
- Lock-in mayor con AWS para el canal telefónico.

### Neutras

- El adaptador de Twilio (`adapters/twilio_transport.py`) y el stack de EC2 se
  conservan: siguen siendo útiles para desarrollo, para el canal web y como
  plan B si se necesitara que el bot telefónico fuese el agente Strands
  (opciones 2/3), sin comprometerse a ello.

## Referencias

- [Use agentic self-service — Amazon Connect admin guide](https://docs.aws.amazon.com/connect/latest/adminguide/agentic-self-service.html)
- [Configure Amazon Nova Sonic Speech-to-Speech — Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/nova-sonic-speech-to-speech.html)
- [Amazon Connect agentic self-service (anuncio, nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-connect-agentic-self-service/)
- Stack de infraestructura: [`infra/terraform/connect`](../../infra/terraform/connect)
