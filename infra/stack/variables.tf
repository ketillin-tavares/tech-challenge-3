# Variaveis do Terraform principal (defaults ja apontam para o projeto real).

variable "project_name" {
  description = "Nome do projeto, usado como prefixo de buckets e tags."
  type        = string
  default     = "tech-challenge-3"
}

variable "aws_region" {
  description = "Regiao AWS onde toda a infraestrutura vive."
  type        = string
  default     = "us-east-2"
}

variable "github_repository" {
  description = "Repositorio GitHub (owner/repo) autorizado a assumir a role de deploy via OIDC."
  type        = string
  default     = "ketillin-tavares/tech-challenge-3"
}

variable "criar_oidc_github" {
  description = "Cria o OIDC provider do GitHub e a role de deploy. Desligado apenas no root local: o emulador floci nao suporta CreateOpenIDConnectProvider (e o deploy via GitHub Actions nao existe no teste local)."
  type        = bool
  default     = true
}

variable "rds_em_vpc" {
  description = "Coloca o RDS nas subnets privadas com o SG dedicado. Desligado apenas no root local: a emulacao de RDS do floci nao enxerga as subnets/SGs da VPC emulada (InvalidSubnet)."
  type        = bool
  default     = true
}

variable "instance_type" {
  description = "Tipo da instancia EC2 (x86_64 para builds nativos nos runners ubuntu)."
  type        = string
  default     = "t3.micro"
}

variable "api_ingress_cidr" {
  description = "CIDR autorizado a acessar as APIs (8000/8001). Padrao aberto por ser um tech challenge avaliado externamente."
  type        = string
  default     = "0.0.0.0/0"
}

variable "db_instance_class" {
  description = "Classe da instancia RDS PostgreSQL."
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Nome do banco de dados do servico de vendas."
  type        = string
  default     = "revenda"
}

variable "db_username" {
  description = "Usuario master do RDS (a senha e gerada e nunca versionada)."
  type        = string
  default     = "revenda"
}
