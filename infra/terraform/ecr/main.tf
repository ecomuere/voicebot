# Stack compartido: repositorio de contenedores usado por los despliegues
# de EC2 y de AgentCore.

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

variable "name" {
  description = "Nombre del repositorio ECR"
  type        = string
  default     = "voicebot"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

resource "aws_ecr_repository" "voicebot" {
  name         = var.name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "repository_url" {
  value = aws_ecr_repository.voicebot.repository_url
}

output "repository_arn" {
  value = aws_ecr_repository.voicebot.arn
}
