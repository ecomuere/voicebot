data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "voicebot" {
  name = var.ecr_repository_name
}

# AMI Amazon Linux 2023 arm64 (la imagen del voicebot es linux/arm64)
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  image_uri = "${data.aws_ecr_repository.voicebot.repository_url}:${var.image_tag}"
}

# ---------------------------------------------------------------------------
# Seguridad: solo HTTP (para el desafío ACME de Caddy) y HTTPS.
# Sin SSH: el acceso a la instancia es vía SSM Session Manager.
# ---------------------------------------------------------------------------

resource "aws_security_group" "voicebot" {
  name        = "${var.name}-ec2"
  description = "Voicebot: HTTP/HTTPS publicos"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP (desafio ACME y redireccion a HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS / WSS (browser y Twilio Media Streams)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------------------------
# Rol de la instancia: pull de ECR, invocar Nova Sonic y acceso por SSM.
# El contenedor obtiene las credenciales AWS automaticamente via IMDS.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "instance" {
  name = "${var.name}-ec2"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "instance" {
  name = "${var.name}-ec2"
  role = aws_iam_role.instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeNovaSonic"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:InvokeModelWithBidirectionalStream",
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*",
        ]
      },
      {
        Sid      = "EcrAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "EcrPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = data.aws_ecr_repository.voicebot.arn
      },
    ]
  })
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.name}-ec2"
  role = aws_iam_role.instance.name
}

# ---------------------------------------------------------------------------
# Instancia + IP elastica
# ---------------------------------------------------------------------------

resource "aws_instance" "voicebot" {
  ami                    = nonsensitive(data.aws_ssm_parameter.al2023_arm64.value)
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.voicebot.id]
  iam_instance_profile   = aws_iam_instance_profile.instance.name

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    region         = var.region
    registry       = split("/", data.aws_ecr_repository.voicebot.repository_url)[0]
    image_uri      = local.image_uri
    domain         = var.domain
    bedrock_region = var.bedrock_region
    voice          = var.voice
    model_id       = var.model_id
  })
  user_data_replace_on_change = true

  tags = { Name = var.name }
}

resource "aws_eip" "voicebot" {
  instance = aws_instance.voicebot.id
  tags     = { Name = var.name }
}
