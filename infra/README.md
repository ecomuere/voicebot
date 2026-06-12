# Infraestructura AWS

IaC en Terraform organizada en stacks independientes — puedes aplicar solo los
que necesites. Todos comparten el repositorio de imágenes del stack `ecr`.

| Stack | Qué despliega | Canales que cubre |
|---|---|---|
| [`terraform/ecr`](terraform/ecr) | Repositorio ECR compartido | — (requisito de ec2 y agentcore) |
| [`terraform/ec2`](terraform/ec2) | EC2 Graviton + Caddy (TLS automático) ejecutando el contenedor | 🌐 Navegador + ☎️ Teléfono (Twilio) con **nuestro agente Strands** |
| [`terraform/agentcore`](terraform/agentcore) | Bedrock AgentCore Runtime (WebSocket bidireccional) | 🌐 Navegador (SigV4/Cognito). Teléfono no directo: Twilio no firma SigV4 |
| [`terraform/connect`](terraform/connect) | Instancia de Connect + número + cola de escalado, routing profile y horario | ☎️ Teléfono con **Nova Sonic nativo de Connect** y escalado a agente humano ([ADR 0001](../docs/adr/0001-telefonia-con-amazon-connect-nativo.md)) |

## Flujo común: construir y publicar la imagen

Los stacks `ec2` y `agentcore` consumen la misma imagen (linux/arm64, puerto
8080, `GET /ping`, WebSocket en `/ws`):

```bash
cd infra/terraform/ecr
terraform init && terraform apply
REPO=$(terraform output -raw repository_url)

# desde la raíz del repo
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "${REPO%%/*}"
docker buildx build --platform linux/arm64 -t "$REPO:latest" --push .
```

## Opción A — EC2 + Twilio (la más directa para teléfono)

```bash
cd infra/terraform/ec2
terraform init
terraform apply -var domain=voicebot.midominio.com
```

1. Crea un registro DNS **A** de tu dominio apuntando al output `public_ip`
   (Caddy emite el certificado TLS solo cuando el DNS resuelve).
2. Navegador: abre el output `web_url`.
3. Teléfono: en Twilio, configura el webhook de voz de tu número con el output
   `twilio_voice_webhook` (POST). No hay SSH; para entrar en la instancia:
   `aws ssm start-session --target <instance_id>`.

## Opción B — AgentCore Runtime (navegador gestionado por AWS)

```bash
cd infra/terraform/agentcore
terraform init && terraform apply
```

El endpoint WebSocket (output `websocket_url`) exige **SigV4**: el navegador
necesita credenciales temporales (Cognito User Pool + Identity Pool, como en el
[ejemplo oficial](https://github.com/aws-samples/sample-nova-sonic-websocket-agentcore))
o un `custom_jwt_authorizer`.

⚠️ **Twilio no puede conectarse directamente a AgentCore** (Media Streams no
firma SigV4 ni envía JWT). Para teléfono con nuestro agente usa la opción A, o
construye un puente proxy que firme SigV4.

## Opción C — Amazon Connect + Nova Sonic nativo

Teléfono sin operar servidores, pero con el agente de IA **de Connect** (la
lógica conversacional se configura en la consola de Connect, no en este repo).
Ver [`terraform/connect/README.md`](terraform/connect/README.md).

## Límites y notas

- Nova Sonic (Bedrock): `us-east-1`, `eu-north-1`, `ap-northeast-1`.
  Nova Sonic en Connect: `us-east-1`, `us-west-2`.
- Sesiones de AgentCore Runtime: hasta 8 h, ~15 min de inactividad.
- Los recursos `bedrockagentcore_*` requieren un provider AWS reciente (v6+, 2026).
- Twilio exige `https://`/`wss://` con certificado válido: en EC2 lo resuelve
  Caddy con Let's Encrypt; en local usa `ngrok http 8000`.
