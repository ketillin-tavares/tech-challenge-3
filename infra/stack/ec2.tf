# =============================================================================
# EC2 unica rodando a stack via docker compose (decisao do projeto).
#   - Amazon Linux 2023 (SSM Agent nativo => zero SSH, deploy via Run Command).
#   - user_data instala apenas Docker + compose plugin; NENHUM segredo aqui:
#     as envs de producao sao resolvidas do SSM em cada deploy (deploy.sh).
#   - IMDSv2 obrigatorio com hop limit 1: containers em bridge NAO alcancam o
#     IMDS (mitiga SSRF no vendas roubando credenciais do instance profile).
#     O auth, unico que precisa do IMDS (boto3/Cognito), roda com
#     network_mode: host no compose de producao.
# =============================================================================

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  metadata_options {
    http_tokens                 = "required" # IMDSv2 obrigatorio
    http_put_response_hop_limit = 1          # bloqueia IMDS p/ containers em bridge (anti-SSRF)
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 16
    encrypted   = true
  }

  # Bootstrap minimo e idempotente; versao do compose pinada conscientemente.
  user_data = <<-EOF
    #!/bin/bash
    set -euo pipefail

    dnf install -y docker
    systemctl enable --now docker

    COMPOSE_VERSION="v2.39.2"
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -fsSL "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Diretorio da aplicacao (compose + .env gerado no deploy; somente root).
    mkdir -p /opt/tc3
    chmod 700 /opt/tc3
  EOF

  tags = { Name = "${local.prefix}-app" }
}

# IP publico estavel (sobrevive a stop/start da instancia).
resource "aws_eip" "app" {
  domain = "vpc"

  tags = { Name = "${local.prefix}-app" }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}

# O workflow de deploy descobre a instancia por aqui (nada hardcoded no GitHub;
# se a instancia for recriada pelo Terraform, o parametro acompanha).
resource "aws_ssm_parameter" "instance_id" {
  name        = "${local.ssm_prefix}/ec2/instance_id"
  description = "Id da instancia EC2 alvo do deploy via SSM Run Command."
  type        = "String"
  value       = aws_instance.app.id
}
