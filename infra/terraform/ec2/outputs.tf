output "public_ip" {
  description = "IP elástica: crea un registro DNS A de var.domain apuntando aquí"
  value       = aws_eip.voicebot.public_ip
}

output "web_url" {
  description = "Cliente web para llamar desde el navegador"
  value       = "https://${var.domain}"
}

output "twilio_voice_webhook" {
  description = "URL a configurar como webhook de voz (POST) del número de Twilio"
  value       = "https://${var.domain}/twilio/voice"
}

output "instance_id" {
  description = "Acceso a la instancia: aws ssm start-session --target <instance_id>"
  value       = aws_instance.voicebot.id
}
