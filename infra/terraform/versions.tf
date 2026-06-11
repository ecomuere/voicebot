terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Los recursos bedrockagentcore_* requieren una versión reciente del provider (v6, 2026).
      version = ">= 6.0"
    }
  }
}

provider "aws" {
  region = var.region
}
