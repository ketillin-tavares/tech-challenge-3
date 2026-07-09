# =============================================================================
# ECR: um repositorio por servico do monorepo (tc3-auth, tc3-vendas).
#   - scan on push (findings de CVE nas imagens).
#   - lifecycle: mantem apenas as 10 imagens mais recentes (custo/higiene).
#   - tags MUTABLE por causa da tag movel `latest` (a tag imutavel de verdade
#     e o SHA do commit, usada pelo deploy).
# =============================================================================

resource "aws_ecr_repository" "services" {
  for_each = toset(["auth", "vendas"])

  name                 = "${local.prefix}-${each.key}"
  image_tag_mutability = "MUTABLE"

  # Tech challenge: permite `terraform destroy` com imagens dentro.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "services" {
  for_each = aws_ecr_repository.services

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Mantem apenas as 10 imagens mais recentes"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}
