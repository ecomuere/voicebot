# Canal telefónico con Amazon Connect + Nova Sonic NATIVO.
#
# Importante: esta opción usa el agente de IA propio de Amazon Connect con
# Nova Sonic (disponible en us-east-1 y us-west-2, con español soportado).
# La lógica conversacional se define en Connect (contact flow + AI agent),
# NO en el contenedor Strands de este repo. Para usar nuestro agente Strands
# detrás de una llamada de Connect haría falta un adaptador de media streaming
# (Kinesis Video Streams) que no está implementado.
#
# Terraform crea la instancia de Connect y reclama un número; el contact flow
# con Nova Sonic se configura en la consola (ver README.md de esta carpeta),
# ya que esa parte aún no está soportada por el provider de Terraform.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "instance_alias" {
  description = "Alias único de la instancia de Connect"
  type        = string
  default     = "voicebot"
}

variable "region" {
  description = "Región (Nova Sonic en Connect: us-east-1 o us-west-2)"
  type        = string
  default     = "us-east-1"
}

variable "phone_number_country_code" {
  description = "País del número a reclamar (ISO, p. ej. US o ES)"
  type        = string
  default     = "US"
}

resource "aws_connect_instance" "voicebot" {
  instance_alias           = var.instance_alias
  identity_management_type = "CONNECT_MANAGED"
  inbound_calls_enabled    = true
  outbound_calls_enabled   = false
}

resource "aws_connect_phone_number" "voicebot" {
  target_arn   = aws_connect_instance.voicebot.arn
  country_code = var.phone_number_country_code
  type         = "DID"
  description  = "Número de entrada del voicebot"
}

output "connect_instance_id" {
  value = aws_connect_instance.voicebot.id
}

output "phone_number" {
  description = "Número de teléfono reclamado (asócialo al contact flow en la consola)"
  value       = aws_connect_phone_number.voicebot.phone_number
}

output "console_url" {
  value = "https://${var.instance_alias}.my.connect.aws"
}
