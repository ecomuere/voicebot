variable "name" {
  description = "Nombre base de los recursos"
  type        = string
  default     = "voicebot"
}

variable "region" {
  description = "Región donde se despliega AgentCore Runtime (y Bedrock/Nova Sonic)"
  type        = string
  default     = "us-east-1"
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

variable "order_status_function_name" {
  description = "Nombre de la Lambda de pedidos (output del stack ../tools); vacío para desactivar la tool"
  type        = string
  default     = ""
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
