# =============================================================================
# CloudWatch Logs: um log group por container da EC2 (auth, vendas, migrations).
#
# Os containers usam o logging driver `awslogs` do Docker (ver
# deploy/docker-compose.prod.yml): o daemon roda no host e envia stdout/stderr
# para ca usando as credenciais do instance profile (tc3-ec2). Somente logs -
# sem metricas nem alarmes (decisao do projeto).
#
# Os grupos sao criados AQUI (e nao pelo driver, awslogs-create-group) para
# manter retencao controlada por codigo e a role da EC2 sem CreateLogGroup.
# =============================================================================

resource "aws_cloudwatch_log_group" "containers" {
  for_each = toset(["auth", "vendas", "migrations"])

  name              = "/${local.prefix}/prod/${each.key}"
  retention_in_days = var.logs_retention_dias
}
