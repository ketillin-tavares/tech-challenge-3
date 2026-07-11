# =============================================================================
# Envs de producao no SSM Parameter Store (prefixo /tc3/prod).
# O deploy.sh (executado na EC2) resolve estes parametros e gera o .env local
# consumido pelo docker-compose.prod.yml. Assim os workflows e o repo nunca
# tocam em segredos: a unica leitura acontece na propria instancia, via IAM.
# =============================================================================

# --- Cognito (auth + vendas) ---------------------------------------------------
resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name        = "${local.ssm_prefix}/cognito/user_pool_id"
  description = "User pool do Cognito (env COGNITO_USER_POOL_ID do auth)."
  type        = "String"
  value       = aws_cognito_user_pool.main.id
}

resource "aws_ssm_parameter" "cognito_client_id" {
  name        = "${local.ssm_prefix}/cognito/client_id"
  description = "App client do Cognito (env COGNITO_CLIENT_ID de auth e vendas)."
  type        = "String"
  value       = aws_cognito_user_pool_client.app.id
}

resource "aws_ssm_parameter" "cognito_issuer" {
  name        = "${local.ssm_prefix}/cognito/issuer"
  description = "Issuer esperado dos JWTs (env COGNITO_ISSUER do vendas)."
  type        = "String"
  value       = local.cognito_issuer
}

resource "aws_ssm_parameter" "cognito_jwks_url" {
  name        = "${local.ssm_prefix}/cognito/jwks_url"
  description = "JWKS do user pool (env JWKS_URL do vendas)."
  type        = "String"
  value       = local.cognito_jwks
}

# --- Banco (vendas + migrations) -------------------------------------------------
# SecureString (KMS aws/ssm): contem a senha do RDS embutida no DSN.
# `ssl=require` cifra o transito ao RDS (asyncpg nao forca TLS por padrao).
resource "aws_ssm_parameter" "database_url" {
  name        = "${local.ssm_prefix}/database/url"
  description = "DSN async do PostgreSQL (env DATABASE_URL do vendas/migrations)."
  type        = "SecureString"
  value       = "postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:5432/${var.db_name}?ssl=require"
}

# --- CORS (auth + vendas) --------------------------------------------------------
# Condicional: SSM nao aceita valor vazio, e sem origem configurada o
# middleware nem e registrado nos servicos (deploy.sh tolera a ausencia).
resource "aws_ssm_parameter" "cors_origins" {
  count = var.cors_origins != "" ? 1 : 0

  name        = "${local.ssm_prefix}/cors/origins"
  description = "Origens permitidas ao frontend (env CORS_ORIGINS de auth e vendas)."
  type        = "String"
  value       = var.cors_origins
}
