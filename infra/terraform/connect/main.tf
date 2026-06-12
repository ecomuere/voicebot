# ---------------------------------------------------------------------------
# Instancia y número
# ---------------------------------------------------------------------------

resource "aws_connect_instance" "voicebot" {
  instance_alias           = var.instance_alias
  identity_management_type = "CONNECT_MANAGED"
  inbound_calls_enabled    = true
  outbound_calls_enabled   = false
}

resource "aws_connect_phone_number" "voicebot" {
  target_arn   = aws_connect_instance.voicebot.arn
  country_code = var.phone_number_country_code
  type         = "DID"
  description  = "Número de entrada del voicebot"
}
