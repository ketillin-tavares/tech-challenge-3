# Outputs do root local (repassados do modulo ../stack) - uteis para inspecao
# do ambiente emulado (IDs do Cognito, endpoint do RDS emulado etc.).

output "gha_deploy_role_arn" {
  description = "Role de deploy criada no emulador."
  value       = module.stack.gha_deploy_role_arn
}

output "app_public_ip" {
  description = "IP publico (EIP) da EC2 emulada."
  value       = module.stack.app_public_ip
}

output "auth_url" {
  description = "URL base do servico de auth (no emulador)."
  value       = module.stack.auth_url
}

output "vendas_url" {
  description = "URL base do servico de vendas (no emulador)."
  value       = module.stack.vendas_url
}

output "cognito_user_pool_id" {
  description = "Id do user pool emulado."
  value       = module.stack.cognito_user_pool_id
}

output "cognito_client_id" {
  description = "Id do app client emulado."
  value       = module.stack.cognito_client_id
}

output "cognito_issuer" {
  description = "Issuer dos JWTs no emulador."
  value       = module.stack.cognito_issuer
}

output "ecr_repository_urls" {
  description = "URLs dos repositorios ECR emulados."
  value       = module.stack.ecr_repository_urls
}

output "deploy_artifacts_bucket" {
  description = "Bucket de artefatos de deploy emulado."
  value       = module.stack.deploy_artifacts_bucket
}

output "rds_endpoint" {
  description = "Endpoint do RDS emulado."
  value       = module.stack.rds_endpoint
}
