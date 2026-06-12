# Herramientas de negocio compartidas (ADR 0001): Lambdas con una única
# implementación de cada regla de negocio, invocadas tanto por el AI agent de
# Amazon Connect (teléfono) como por el agente Strands (web).

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "name" {
  description = "Prefijo de los recursos (debe coincidir con el de los demás stacks)"
  type        = string
  default     = "voicebot"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "connect_instance_arn" {
  description = <<-EOT
    ARN de la instancia de Amazon Connect (output del stack ../connect).
    Si se define, la Lambda se asocia a la instancia para poder invocarla
    desde el contact flow / AI agent. Null para omitir.
  EOT
  type        = string
  default     = null
}

locals {
  connect_enabled     = var.connect_instance_arn != null
  connect_instance_id = local.connect_enabled ? element(split("/", var.connect_instance_arn), 1) : null
}

# ---------------------------------------------------------------------------
# Lambda: estado de pedidos (código en lambdas/order_status)
# ---------------------------------------------------------------------------

data "archive_file" "order_status" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambdas/order_status"
  output_path = "${path.module}/.build/order_status.zip"
  excludes    = ["__pycache__"]
}

resource "aws_iam_role" "order_status" {
  name = "${var.name}-order-status"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "order_status_logs" {
  role       = aws_iam_role.order_status.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "order_status" {
  function_name    = "${var.name}-order-status"
  description      = "Herramienta compartida: estado de pedidos (Connect + Strands)"
  role             = aws_iam_role.order_status.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.order_status.output_path
  source_code_hash = data.archive_file.order_status.output_base64sha256
  timeout          = 10
}

# ---------------------------------------------------------------------------
# Integración con Amazon Connect (opcional)
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "connect" {
  count = local.connect_enabled ? 1 : 0

  statement_id  = "AllowAmazonConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.order_status.function_name
  principal     = "connect.amazonaws.com"
  source_arn    = var.connect_instance_arn
}

resource "aws_connect_lambda_function_association" "order_status" {
  count = local.connect_enabled ? 1 : 0

  instance_id  = local.connect_instance_id
  function_arn = aws_lambda_function.order_status.arn
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "order_status_function_name" {
  description = "Valor para VOICEBOT_ORDER_STATUS_FUNCTION en los stacks ec2/agentcore"
  value       = aws_lambda_function.order_status.function_name
}

output "order_status_function_arn" {
  value = aws_lambda_function.order_status.arn
}
