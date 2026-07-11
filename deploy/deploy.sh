#!/usr/bin/env bash
# =============================================================================
# Deploy na EC2 (executado como root pelo SSM Run Command; ver deploy.yml).
#
# Fluxo:
#   1. Resolve as envs de producao do SSM Parameter Store (/tc3/prod/*) e gera
#      /opt/tc3/.env (0600) - consumido pelo compose (interpolacao + env_file).
#   2. Login no ECR com as credenciais do instance profile (IMDSv2).
#   3. Pull das imagens do commit e `compose up`: migrations (one-shot) e as
#      APIs vendas/auth. `--wait` falha o deploy se algum healthcheck nao subir.
#
# Uso: deploy.sh <image_tag>   (tag = SHA do commit publicado no ECR)
# =============================================================================
set -euo pipefail

IMAGE_TAG="${1:?uso: deploy.sh <image_tag>}"
APP_DIR="/opt/tc3"
SSM_PREFIX="/tc3/prod"

# Regiao unica do projeto (mesma dos defaults do Terraform).
export AWS_DEFAULT_REGION="us-east-2"

get_param() {
  aws ssm get-parameter --name "${SSM_PREFIX}/$1" --with-decryption \
    --query 'Parameter.Value' --output text
}

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"

# --- 1. .env de producao (somente root; nunca commitado) ----------------------
umask 077
cat > "${APP_DIR}/.env" <<EOF
# Gerado pelo deploy.sh a partir do SSM Parameter Store. NAO editar/commitar.
ECR_REGISTRY=${ECR_REGISTRY}
IMAGE_TAG=${IMAGE_TAG}
ENVIRONMENT=production
LOG_LEVEL=INFO
AWS_REGION=${AWS_DEFAULT_REGION}
COGNITO_USER_POOL_ID=$(get_param cognito/user_pool_id)
COGNITO_CLIENT_ID=$(get_param cognito/client_id)
COGNITO_ISSUER=$(get_param cognito/issuer)
JWKS_URL=$(get_param cognito/jwks_url)
DATABASE_URL=$(get_param database/url)
CORS_ORIGINS=$(get_param cors/origins 2>/dev/null || true)
EOF

# --- 2. Login no ECR (token efemero via instance profile) ---------------------
aws ecr get-login-password | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

# --- 3. Sobe a stack (migrations one-shot -> vendas; auth independente) -------
cd "${APP_DIR}"
docker compose -f docker-compose.prod.yml pull --quiet
docker compose -f docker-compose.prod.yml up -d --remove-orphans --wait --wait-timeout 300

docker logout "${ECR_REGISTRY}"
# Higiene de disco: remove imagens antigas nao utilizadas.
docker image prune -f

echo "deploy concluido: tag ${IMAGE_TAG}"
