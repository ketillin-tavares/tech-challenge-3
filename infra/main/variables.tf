# Variaveis do root de producao (defaults ja apontam para o projeto real).
# As demais variaveis do stack (instancias, banco etc.) usam os defaults do
# modulo em infra/stack/variables.tf.

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
