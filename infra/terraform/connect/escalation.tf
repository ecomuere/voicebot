# ---------------------------------------------------------------------------
# Lado humano del escalado (ADR 0001): horario, cola, routing profile y
# usuario agente opcional. El contact flow con el AI agent (Nova Sonic)
# transfiere a esta cola cuando el llamante pide hablar con una persona.
# ---------------------------------------------------------------------------

locals {
  weekdays = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
}

resource "aws_connect_hours_of_operation" "support" {
  instance_id = aws_connect_instance.voicebot.id
  name        = "Horario de soporte"
  description = "Franja en la que hay agentes humanos disponibles"
  time_zone   = var.time_zone

  dynamic "config" {
    for_each = local.weekdays
    content {
      day = config.value
      start_time {
        hours   = var.business_hours.start_hour
        minutes = 0
      }
      end_time {
        hours   = var.business_hours.end_hour
        minutes = 0
      }
    }
  }
}

resource "aws_connect_queue" "human_escalation" {
  instance_id           = aws_connect_instance.voicebot.id
  name                  = "escalado-humano"
  description           = "Cola a la que el AI agent transfiere cuando el llamante pide un humano"
  hours_of_operation_id = aws_connect_hours_of_operation.support.hours_of_operation_id
}

resource "aws_connect_routing_profile" "human_agents" {
  instance_id               = aws_connect_instance.voicebot.id
  name                      = "agentes-humanos"
  description               = "Routing profile de los agentes que atienden el escalado del voicebot"
  default_outbound_queue_id = aws_connect_queue.human_escalation.queue_id

  media_concurrencies {
    channel     = "VOICE"
    concurrency = 1
  }

  queue_configs {
    channel  = "VOICE"
    delay    = 0
    priority = 1
    queue_id = aws_connect_queue.human_escalation.queue_id
  }
}

# Perfil de seguridad estándar "Agent" que Connect crea con la instancia.
data "aws_connect_security_profile" "agent" {
  instance_id = aws_connect_instance.voicebot.id
  name        = "Agent"
}

resource "aws_connect_user" "sample_agent" {
  count = var.agent_username == null ? 0 : 1

  instance_id          = aws_connect_instance.voicebot.id
  name                 = var.agent_username
  password             = var.agent_password
  routing_profile_id   = aws_connect_routing_profile.human_agents.routing_profile_id
  security_profile_ids = [data.aws_connect_security_profile.agent.security_profile_id]

  identity_info {
    first_name = var.agent_first_name
    last_name  = var.agent_last_name
  }

  phone_config {
    phone_type                    = "SOFT_PHONE"
    auto_accept                   = false
    after_contact_work_time_limit = 60
  }
}
