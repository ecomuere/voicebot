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

variable "time_zone" {
  description = "Zona horaria del horario de atención humana"
  type        = string
  default     = "Europe/Madrid"
}

variable "business_hours" {
  description = "Franja de atención humana en días laborables (horas, 0-23)"
  type = object({
    start_hour = number
    end_hour   = number
  })
  default = {
    start_hour = 9
    end_hour   = 18
  }
}

# Usuario agente de ejemplo (opcional): déjalo a null para no crearlo y dar
# de alta a los agentes humanos desde la consola.
variable "agent_username" {
  description = "Login del agente humano de ejemplo (null = no crear)"
  type        = string
  default     = null
}

variable "agent_password" {
  description = "Contraseña inicial del agente de ejemplo (mín. 8 caracteres, mayúscula, minúscula y número)"
  type        = string
  default     = null
  sensitive   = true
}

variable "agent_first_name" {
  type    = string
  default = "Agente"
}

variable "agent_last_name" {
  type    = string
  default = "Humano"
}
