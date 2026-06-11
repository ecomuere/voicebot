output "ecr_repository_url" {
  description = "URI del repositorio ECR donde subir la imagen"
  value       = data.aws_ecr_repository.voicebot.repository_url
}

output "agent_runtime_arn" {
  description = "ARN del AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.voicebot.agent_runtime_arn
}

output "agent_runtime_id" {
  description = "ID del AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.voicebot.agent_runtime_id
}

output "websocket_url" {
  description = "Endpoint WebSocket del runtime (requiere firma SigV4)"
  value = format(
    "wss://bedrock-agentcore.%s.amazonaws.com/runtimes/%s/ws?qualifier=DEFAULT",
    var.region,
    urlencode(aws_bedrockagentcore_agent_runtime.voicebot.agent_runtime_arn),
  )
}
