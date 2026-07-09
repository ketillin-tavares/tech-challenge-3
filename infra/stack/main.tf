# =============================================================================
# Modulo compartilhado da infraestrutura ("stack"): TODOS os recursos AWS do
# projeto, definidos UMA unica vez. Sem provider e sem backend/cloud aqui -
# isso e responsabilidade dos roots finos:
#   - infra/main:  AWS real (execucao remota + state no HCP Terraform).
#   - infra/local: emulador floci (localhost:4566) para testar o deploy
#                  localmente antes de gastar AWS real.
#
# Recursos: rede (VPC/SGs), EC2 (docker compose), RDS PostgreSQL, Cognito,
# ECR, S3 (artefatos de deploy), SSM Parameter Store, OIDC provider do GitHub
# e roles IAM (tc3-ec2, tc3-gha-deploy, permissions boundary).
# =============================================================================

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  account_id = data.aws_caller_identity.current.account_id
  # Prefixo curto dos recursos do projeto.
  prefix = "tc3"
  # Prefixo dos parametros de producao no SSM Parameter Store.
  ssm_prefix = "/tc3/prod"
  # Sub do token OIDC: somente a branch main do repo assume a role de deploy.
  github_oidc_sub = "repo:${var.github_repository}:ref:refs/heads/main"
}
