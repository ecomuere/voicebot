variable "name" {
  description = "Nombre base de los recursos"
  type        = string
  default     = "voicebot"
}

variable "region" {
  description = "Región donde se despliega la instancia"
  type        = string
  default     = "us-east-1"
}

variable "bedrock_region" {
  description = "Región de Bedrock con Nova Sonic (us-east-1, eu-north-1 o ap-northeast-1)"
  type        = string
  default     = "us-east-1"
}

variable "domain" {
  description = <<-EOT
    Dominio público del voicebot (p. ej. voicebot.midominio.com). Tras el apply,
    crea un registro DNS A apuntando a la IP elástica del output; Caddy emitirá
    el certificado TLS automáticamente (Twilio y el micrófono del navegador
    exigen HTTPS/WSS).
  EOT
  type        = string
}

variable "instance_type" {
  description = "Tipo de instancia (Graviton/arm64, la imagen es linux/arm64)"
  type        = string
  default     = "t4g.small"
}

variable "ecr_repository_name" {
  description = "Nombre del repositorio ECR (creado por el stack ../ecr)"
  type        = string
  default     = "voicebot"
}

variable "image_tag" {
  description = "Tag de la imagen del contenedor en ECR"
  type        = string
  default     = "latest"
}

variable "voice" {
  description = "Voz de Nova Sonic (VOICEBOT_VOICE)"
  type        = string
  default     = "tiffany"
}

variable "model_id" {
  description = "Modelo speech-to-speech de Bedrock"
  type        = string
  default     = "amazon.nova-sonic-v1:0"
}
