# =============================================================================
# Cognito gerenciado pelo Terraform (substitui o user pool criado manualmente).
# Configuracao espelha o que o codigo dos servicos espera:
#   - auth: SignUp com Username=email + AdminConfirmSignUp (auto-confirmacao)
#     e login via InitiateAuth USER_PASSWORD_AUTH => app client SEM secret.
#   - vendas: valida access tokens (iss + claim client_id + cognito:groups).
# =============================================================================

resource "aws_cognito_user_pool" "main" {
  name = "${local.prefix}-users"

  # O codigo registra com Username = e-mail.
  username_attributes = ["email"]

  # Alinhada ao dominio (Senha: min_length=8). Politica mais rigida no pool
  # geraria InvalidPasswordException nao mapeada pelo gateway (HTTP 500).
  password_policy {
    minimum_length                   = 8
    require_lowercase                = false
    require_numbers                  = false
    require_symbols                  = false
    require_uppercase                = false
    temporary_password_validity_days = 7
  }

  # Sem fluxo de recuperacao self-service (nao ha envio de e-mail no projeto).
  account_recovery_setting {
    recovery_mechanism {
      name     = "admin_only"
      priority = 1
    }
  }

  # Tech challenge: permite `terraform destroy` limpo.
  deletion_protection = "INACTIVE"

  tags = { Name = "${local.prefix}-users" }
}

resource "aws_cognito_user_pool_client" "app" {
  name         = "${local.prefix}-app"
  user_pool_id = aws_cognito_user_pool.main.id

  # SEM client secret: o auth usa InitiateAuth USER_PASSWORD_AUTH puro.
  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  # Nao revela se o usuario existe (o gateway ja trata NotAuthorizedException).
  prevent_user_existence_errors = "ENABLED"
}

# Membros deste grupo (claim cognito:groups) podem gerenciar veiculos no vendas.
resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Administradores: gestao de veiculos no servico de vendas."
}

locals {
  cognito_issuer = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
  cognito_jwks   = "${local.cognito_issuer}/.well-known/jwks.json"
}
