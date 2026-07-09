# =============================================================================
# Root de PRODUCAO (CLI-driven via GitHub Actions + HCP Terraform).
#
# O workflow .github/workflows/infra.yml roda `terraform plan/apply` daqui,
# mas a EXECUCAO e o STATE ficam no HCP Terraform (app.terraform.io): o runner
# so dispara e acompanha o run remoto. As credenciais AWS vivem como
# environment variables *sensitive* no workspace (trade-off consciente do
# projeto: chaves estaticas no TFC em vez de OIDC no runner) - o job de infra
# nao toca a AWS.
#
# Os recursos vivem no modulo compartilhado ../stack (mesma definicao usada
# pelo root local infra/local, que aponta para o emulador floci).
# =============================================================================

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # HCP Terraform: organizacao e workspace NAO ficam chumbados aqui - vem das
  # env vars TF_CLOUD_ORGANIZATION e TF_WORKSPACE (suporte nativo do Terraform
  # >= 1.6), injetadas pelo infra.yml a partir das GitHub variables. Motivo: a
  # org ainda nao existia quando este codigo foi escrito; env var evita
  # placeholder quebrado no repo e permite trocar de org sem editar codigo.
  cloud {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

module "stack" {
  source = "../stack"

  project_name = var.project_name
  aws_region   = var.aws_region
}
