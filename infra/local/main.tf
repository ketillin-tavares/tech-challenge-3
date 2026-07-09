# =============================================================================
# Root LOCAL (floci): o MESMO stack de producao apontando para o emulador AWS
# local (https://floci.io) em http://localhost:4566 - testa o provisionamento
# completo sem gastar AWS real.
#
# Uso (ver infra/local/README.md):
#   docker compose up -d floci   (na raiz do repo)
#   cd infra/local && terraform init && terraform apply
#
# Decisoes deste root:
#   - State LOCAL (terraform.tfstate nesta pasta; ignorado no git) - nunca
#     mistura com o state de producao do HCP Terraform.
#   - Endpoints e credenciais dummy CHUMBADOS de proposito (sem export de env
#     vars): apontam para o emulador, nunca para a AWS real.
# =============================================================================

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  # Credenciais dummy: o floci nao valida; jamais alcancam a AWS real.
  access_key = "test"
  secret_key = "test"
  region     = "us-east-2"

  # Evita chamadas de validacao contra a AWS real.
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true

  # Sem default_tags no emulador: o IAM do floci nao suporta TagInstanceProfile
  # e as tags nao tem valor num ambiente descartavel. O ignore_tags evita que o
  # provider tente REMOVER tags ja aplicadas em runs anteriores.
  ignore_tags {
    keys = ["Project", "ManagedBy"]
  }

  # Todos os servicos usados pelo stack -> emulador local.
  # ATENCAO: qualquer servico fora desta lista vaza para a AWS real (falha com
  # AccessDenied pelas credenciais dummy, mas gera chamadas externas). O
  # `s3control` e um servico DISTINTO do `s3` no provider e e usado pela
  # leitura de tags de buckets no provider v6 - sem ele o apply vazava.
  endpoints {
    ec2        = "http://localhost:4566"
    rds        = "http://localhost:4566"
    cognitoidp = "http://localhost:4566"
    ecr        = "http://localhost:4566"
    ssm        = "http://localhost:4566"
    s3         = "http://localhost:4566"
    # O SDK do s3control prefixa o account id no HOSTNAME (000000000000.<host>),
    # e `000000000000.localhost` nao resolve. `*.localhost.localstack.cloud` e
    # um DNS publico wildcard -> 127.0.0.1 (mesma porta do emulador).
    s3control = "http://localhost.localstack.cloud:4566"
    iam       = "http://localhost:4566"
    sts       = "http://localhost:4566"
  }
}

# Mesmas definicoes de producao (variaveis nos defaults do modulo), exceto os
# contornos de limitacoes do emulador (documentados nas proprias variaveis):
#   - criar_oidc_github: floci nao suporta CreateOpenIDConnectProvider (e o
#     deploy via GitHub Actions nao faz parte do teste local).
#   - rds_em_vpc: o RDS do floci nao enxerga as subnets da VPC emulada.
module "stack" {
  source = "../stack"

  criar_oidc_github = false
  rds_em_vpc        = false
}
