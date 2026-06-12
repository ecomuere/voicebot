# Canal telefónico con Amazon Connect + Nova Sonic NATIVO (ver ADR 0001).
#
# La llamada comienza con el AI agent de Connect (Nova Sonic) y escala a la
# cola humana definida aquí. La lógica conversacional se define en Connect
# (contact flow + AI agent), NO en el contenedor Strands de este repo.
#
# Terraform cubre: instancia, número, horario, cola de escalado, routing
# profile y (opcional) un usuario agente. El contact flow con el bloque de
# AI agent se configura en la consola (ver README.md), ya que esa parte aún
# no está soportada por el provider.

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
