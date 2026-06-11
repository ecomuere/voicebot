data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  # El nombre del runtime solo admite [a-zA-Z][a-zA-Z0-9_]*
  runtime_name = replace(var.name, "-", "_")
}

# ---------------------------------------------------------------------------
# Registro de contenedores
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "voicebot" {
  name         = var.name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ---------------------------------------------------------------------------
# Rol de ejecución del runtime
# ---------------------------------------------------------------------------

resource "aws_iam_role" "runtime" {
  name = "${var.name}-agentcore-runtime"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock-agentcore.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = local.account_id }
      }
    }]
  })
}

resource "aws_iam_role_policy" "runtime" {
  name = "${var.name}-agentcore-runtime"
  role = aws_iam_role.runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeNovaSonic"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:InvokeModelWithBidirectionalStream",
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:${local.account_id}:inference-profile/*",
        ]
      },
      {
        Sid      = "EcrAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "EcrPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = aws_ecr_repository.voicebot.arn
      },
      {
        Sid    = "Logs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
        ]
        Resource = "arn:aws:logs:${var.region}:${local.account_id}:log-group:/aws/bedrock-agentcore/*"
      },
      {
        Sid    = "Telemetry"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "cloudwatch:PutMetricData",
        ]
        Resource = "*"
      },
      {
        Sid    = "WorkloadIdentity"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:GetWorkloadAccessToken",
          "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
          "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
        ]
        Resource = "arn:aws:bedrock-agentcore:${var.region}:${local.account_id}:workload-identity-directory/default*"
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# AgentCore Runtime
#
# El contenedor debe escuchar en el puerto 8080 (arquitectura arm64) y exponer:
#   GET /ping  -> health check
#   WS  /ws    -> streaming bidireccional de audio
# Con server_protocol = "HTTP" el runtime publica tanto /invocations (REST)
# como /ws (WebSocket bidireccional).
# ---------------------------------------------------------------------------

resource "aws_bedrockagentcore_agent_runtime" "voicebot" {
  agent_runtime_name = local.runtime_name
  description        = "Voicebot speech-to-speech (Strands + Nova Sonic)"
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.voicebot.repository_url}:${var.image_tag}"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  protocol_configuration {
    server_protocol = "HTTP"
  }

  environment_variables = {
    VOICEBOT_REGION   = var.region
    VOICEBOT_VOICE    = var.voice
    VOICEBOT_MODEL_ID = var.model_id
  }

  depends_on = [aws_iam_role_policy.runtime]
}
