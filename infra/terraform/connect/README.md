# Canal telefónico con Amazon Connect + Nova Sonic (nativo)

Esta opción **no usa el contenedor Strands del repo**: desde re:Invent 2025,
Amazon Connect integra Nova Sonic de forma nativa en sus contact flows
("agentic self-service"). La conversación speech-to-speech la gestiona el
agente de IA de Connect, configurado en la consola de Connect.

- ✅ Sin servidor que operar, número incluido, integración 100 % AWS.
- ⚠️ La lógica del agente (prompt, herramientas) se define en Connect, no en
  este repo. Disponible en `us-east-1` y `us-west-2`; español soportado.
- ⚠️ Si quieres que sea **nuestro** agente Strands quien atienda llamadas de
  Connect, haría falta un adaptador de media streaming (Kinesis Video
  Streams) que no está implementado — usa la opción EC2 + Twilio para eso.

## Despliegue

```bash
terraform init
terraform apply
```

Crea la instancia de Connect y reclama un número (output `phone_number`).

## Configuración en consola (no soportada aún por Terraform)

1. Entra en la consola de Connect (output `console_url`) y crea un usuario admin.
2. Crea un **contact flow** de entrada y añade un bloque de conversación con IA:
   en *Speech model* elige **Speech-to-Speech** → proveedor **Amazon Nova Sonic**,
   activa **Enable AI Agent** y selecciona una voz compatible (hay voces en español).
3. Define el AI agent (instrucciones del sistema, acciones/herramientas).
4. Asocia el número reclamado al contact flow (Channels → Phone numbers).
5. Llama al número.

Referencias:
- [Configure Amazon Nova Sonic Speech-to-Speech (Connect admin guide)](https://docs.aws.amazon.com/connect/latest/adminguide/nova-sonic-speech-to-speech.html)
- [Amazon Connect agentic self-service (anuncio)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-connect-agentic-self-service/)
