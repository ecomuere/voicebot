output "connect_instance_id" {
  value = aws_connect_instance.voicebot.id
}

output "connect_instance_arn" {
  description = "Pásalo como connect_instance_arn al stack ../tools para asociar las Lambdas"
  value       = aws_connect_instance.voicebot.arn
}

output "phone_number" {
  description = "Número de teléfono reclamado (asócialo al contact flow en la consola)"
  value       = aws_connect_phone_number.voicebot.phone_number
}

output "console_url" {
  value = "https://${var.instance_alias}.my.connect.aws"
}

output "escalation_queue_name" {
  description = "Cola a seleccionar en el bloque 'Set working queue' del contact flow"
  value       = aws_connect_queue.human_escalation.name
}

output "escalation_queue_arn" {
  value = aws_connect_queue.human_escalation.arn
}

output "routing_profile_name" {
  description = "Routing profile a asignar a los agentes humanos"
  value       = aws_connect_routing_profile.human_agents.name
}
