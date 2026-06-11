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
