# =============================================================================
# Bucket de artefatos de deploy: o workflow deploy.yml publica o
# docker-compose.prod.yml + deploy.sh aqui e a EC2 os baixa via SSM Run Command
# (evita colar arquivos inteiros dentro do comando SSM).
# =============================================================================

resource "aws_s3_bucket" "deploy_artifacts" {
  bucket = "${var.project_name}-deploy-${local.account_id}"

  # Tech challenge: permite `terraform destroy` sem esvaziar o bucket antes.
  force_destroy = true
}

# Versionamento: trilha de auditoria/rollback do deploy.sh (executa como root
# na EC2) e do compose de producao.
resource "aws_s3_bucket_versioning" "deploy_artifacts" {
  bucket = aws_s3_bucket.deploy_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deploy_artifacts" {
  bucket = aws_s3_bucket.deploy_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "deploy_artifacts" {
  bucket = aws_s3_bucket.deploy_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Nega qualquer acesso sem TLS (criptografia em transito obrigatoria).
data "aws_iam_policy_document" "deploy_artifacts_tls_only" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.deploy_artifacts.arn,
      "${aws_s3_bucket.deploy_artifacts.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "deploy_artifacts" {
  bucket = aws_s3_bucket.deploy_artifacts.id
  policy = data.aws_iam_policy_document.deploy_artifacts_tls_only.json

  # O public access block precisa existir antes de anexar a policy.
  depends_on = [aws_s3_bucket_public_access_block.deploy_artifacts]
}
