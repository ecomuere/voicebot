# Infraestructura AWS (Bedrock AgentCore Runtime)

Terraform que despliega el voicebot como **Bedrock AgentCore Runtime** con
streaming bidireccional por WebSocket:

- Repositorio **ECR** para la imagen del contenedor.
- **Rol IAM** de ejecución (invocar Nova Sonic, pull de ECR, logs, telemetría).
- **AgentCore Runtime** (`aws_bedrockagentcore_agent_runtime`) con red pública
  y protocolo `HTTP`, que publica `/invocations` (REST) y `/ws` (WebSocket).

El contrato de servicio de AgentCore que cumple la app (`Dockerfile`):
contenedor **linux/arm64**, puerto **8080**, health check **`GET /ping`** y
WebSocket bidireccional en **`/ws`**.

## Despliegue

Hay dependencia circular suave: el runtime necesita que la imagen exista en ECR.
Por eso el primer `apply` se hace en dos pasos.

```bash
cd infra/terraform
terraform init

# 1. Crear solo el repositorio ECR
terraform apply -target=aws_ecr_repository.voicebot

# 2. Construir y subir la imagen (arm64) desde la raíz del repo
REPO=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "${REPO%%/*}"
docker buildx build --platform linux/arm64 -t "$REPO:latest" --push ../..

# 3. Crear el resto (rol IAM + runtime)
terraform apply
```

Para actualizar el agente: vuelve a construir/subir la imagen y ejecuta
`terraform apply` (o fuerza una nueva versión del runtime cambiando `image_tag`).

## Conectarse al runtime

El endpoint WebSocket (output `websocket_url`) está protegido con **IAM SigV4**:
cada conexión debe ir firmada con credenciales AWS.

- **Navegador**: el patrón recomendado de AWS es Cognito (User Pool + Identity
  Pool) para obtener credenciales temporales en el cliente y firmar la conexión
  WebSocket, como en el ejemplo oficial
  [sample-nova-sonic-websocket-agentcore](https://github.com/aws-samples/sample-nova-sonic-websocket-agentcore).
  Alternativa: `authorizer_configuration` con JWT (custom_jwt_authorizer).
- **Pruebas rápidas**: un cliente Python/Node con tus credenciales locales
  firmando SigV4 contra `websocket_url`.

### ⚠️ Telefonía (Twilio) y AgentCore

Twilio Media Streams **no puede firmar SigV4 ni adjuntar JWT** en la conexión
WebSocket, así que no puede conectarse directamente al runtime. Opciones:

1. **Híbrido (recomendado para empezar)**: el canal de navegador en AgentCore y
   el canal telefónico self-hosted (el mismo contenedor en ECS Fargate/EC2
   detrás de un ALB, o con ngrok en desarrollo). Es el mismo código.
2. **Puente**: un pequeño proxy público (Fargate/API Gateway) que acepte el
   WebSocket de Twilio y reenvíe el audio al runtime firmando SigV4.
3. **Amazon Connect** en lugar de Twilio, que se integra de forma nativa con
   servicios AWS.

## Límites a tener en cuenta

- Sesiones de AgentCore Runtime: hasta 8 h de duración y ~15 min de inactividad.
- Nova Sonic está disponible en `us-east-1`, `eu-north-1` y `ap-northeast-1`.
- Los recursos `bedrockagentcore_*` requieren una versión reciente del provider
  AWS de Terraform (v6+, 2026).
