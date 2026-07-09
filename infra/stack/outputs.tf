# Outputs do Terraform principal.
# `gha_deploy_role_arn` deve virar a GitHub variable AWS_DEPLOY_ROLE_ARN.

output "gha_deploy_role_arn" {
  description = "Role do workflow de deploy -> variable AWS_DEPLOY_ROLE_ARN no GitHub. Null no root local (criar_oidc_github = false)."
  value       = one(aws_iam_role.gha_deploy[*].arn)
}

output "app_public_ip" {
  description = "IP publico (EIP) da EC2 da aplicacao."
  value       = aws_eip.app.public_ip
}

output "auth_url" {
  description = "URL base do servico de auth."
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "vendas_url" {
  description = "URL base do servico de vendas."
  value       = "http://${aws_eip.app.public_ip}:8001"
}

output "cognito_user_pool_id" {
  description = "Id do user pool (COGNITO_USER_POOL_ID para .env locais)."
  value       = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  description = "Id do app client (COGNITO_CLIENT_ID para .env locais)."
  value       = aws_cognito_user_pool_client.app.id
}

output "cognito_issuer" {
  description = "Issuer dos JWTs (COGNITO_ISSUER para .env locais)."
  value       = local.cognito_issuer
}

output "ecr_repository_urls" {
  description = "URLs dos repositorios ECR por servico."
  value       = { for name, repo in aws_ecr_repository.services : name => repo.repository_url }
}

output "deploy_artifacts_bucket" {
  description = "Bucket com os artefatos de deploy (compose + script)."
  value       = aws_s3_bucket.deploy_artifacts.bucket
}

output "rds_endpoint" {
  description = "Endpoint do RDS (privado; acessivel apenas pela EC2)."
  value       = aws_db_instance.main.address
}
