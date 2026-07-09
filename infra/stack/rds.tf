# =============================================================================
# RDS PostgreSQL de producao (servico de vendas).
#   - Single-AZ, db.t3.micro, 20 GiB gp3 (minimo) -> menor custo possivel.
#   - Privado (subnets sem rota de internet) e restrito ao SG da EC2.
#   - Senha gerada pelo Terraform (random_password) e exposta SOMENTE via SSM
#     SecureString (ssm.tf); nunca em texto plano no repo/workflows.
# =============================================================================

# Sem caracteres especiais: a senha entra na DATABASE_URL (DSN) e a ausencia de
# especiais evita URL-encoding e os caracteres proibidos pelo RDS (/ @ " espaco).
# 32 chars alfanumericos ~ 190 bits de entropia: mais que suficiente.
resource "random_password" "db" {
  length  = 32
  special = false
}

# Condicional (var.rds_em_vpc): o root local desliga porque o RDS do floci
# nao enxerga as subnets da VPC emulada.
resource "aws_db_subnet_group" "main" {
  count = var.rds_em_vpc ? 1 : 0

  name       = "${local.prefix}-rds"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${local.prefix}-rds" }
}

resource "aws_db_instance" "main" {
  identifier     = "${local.prefix}-postgres"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = var.rds_em_vpc ? aws_db_subnet_group.main[0].name : null
  vpc_security_group_ids = var.rds_em_vpc ? [aws_security_group.rds.id] : null
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period    = 1
  auto_minor_version_upgrade = true

  # Tech challenge: permite `terraform destroy` limpo.
  skip_final_snapshot = true
  deletion_protection = false

  tags = { Name = "${local.prefix}-postgres" }
}
