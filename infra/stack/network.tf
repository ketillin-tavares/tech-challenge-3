# =============================================================================
# Rede: VPC enxuta, SEM NAT Gateway (custo zero de NAT).
#   - Subnet publica: EC2 (egress via Internet Gateway; ingress fechado no SG).
#   - Subnets privadas (2 AZs, exigencia do DB subnet group): RDS sem rota de
#     internet, alcancavel apenas pelo SG da EC2 na porta 5432.
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.prefix}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${local.prefix}-igw" }
}

# --- Subnet publica (EC2) -----------------------------------------------------
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = { Name = "${local.prefix}-public" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${local.prefix}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# --- Subnets privadas (RDS) ---------------------------------------------------
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${10 + count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "${local.prefix}-private-${count.index}" }
}

# Route table SEM rota default: subnets privadas ficam sem acesso a internet.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${local.prefix}-private" }
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --- Security Groups ----------------------------------------------------------
# EC2: somente as portas das APIs. SEM porta 22 (acesso administrativo e deploy
# acontecem exclusivamente via SSM Session Manager / Run Command).
resource "aws_security_group" "ec2" {
  name        = "${local.prefix}-ec2"
  description = "APIs auth (8000) e vendas (8001); sem SSH"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "API auth"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.api_ingress_cidr]
  }

  ingress {
    description = "API vendas"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = [var.api_ingress_cidr]
  }

  # Egress liberado: ECR/SSM/Cognito/JWKS via internet (sem VPC endpoints).
  egress {
    description = "Saida geral (ECR, SSM, Cognito, JWKS)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.prefix}-ec2" }
}

# RDS: aceita 5432 APENAS do SG da EC2; sem egress (respostas sao stateful).
resource "aws_security_group" "rds" {
  name        = "${local.prefix}-rds"
  description = "PostgreSQL somente a partir da EC2"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL a partir da EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  tags = { Name = "${local.prefix}-rds" }
}
