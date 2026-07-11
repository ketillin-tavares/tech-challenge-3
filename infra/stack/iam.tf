# =============================================================================
# IAM (menor privilegio):
#   - tc3-permissions-boundary: teto de permissoes de QUALQUER role tc3-*.
#     O IAM user do TFC so pode criar roles com esta boundary anexada (ver
#     infra/tfc-user-policy.json), entao mesmo uma role tc3-* criada com
#     policy arbitraria nao escala alem deste teto.
#   - tc3-ec2: role da instancia (SSM gerenciado + ECR pull + leitura dos
#     parametros /tc3/prod/* + AdminConfirmSignUp no user pool). O servico de
#     auth usa o instance profile via IMDSv2 (sem chaves estaticas em .env).
#   - tc3-gha-deploy: role do workflow deploy.yml via OIDC (ECR push + upload
#     dos artefatos de deploy no S3 + SSM SendCommand APENAS nesta instancia).
# =============================================================================

# --- Permissions boundary das roles tc3-* -----------------------------------------
# Uniao do que tc3-ec2 e tc3-gha-deploy realmente usam (ECR, SSM agent/params/
# Run Command, S3 do projeto, Cognito). Boundary e TETO, nao concessao: as
# permissoes efetivas continuam sendo as policies (mais restritas) das roles.
data "aws_iam_policy_document" "permissions_boundary" {
  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid       = "EcrProjectRepos"
    effect    = "Allow"
    actions   = ["ecr:*"]
    resources = ["arn:aws:ecr:${var.aws_region}:${local.account_id}:repository/${local.prefix}-*"]
  }

  statement {
    sid    = "SsmProjectParams"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]
    resources = ["arn:aws:ssm:${var.aws_region}:${local.account_id}:parameter${local.ssm_prefix}/*"]
  }

  # SSM agent (AmazonSSMManagedInstanceCore) + Run Command do deploy.
  statement {
    sid    = "SsmAgentAndRunCommand"
    effect = "Allow"
    actions = [
      "ssm:DescribeAssociation",
      "ssm:DescribeDocument",
      "ssm:GetDocument",
      "ssm:GetManifest",
      "ssm:GetDeployablePatchSnapshotForInstance",
      "ssm:ListAssociations",
      "ssm:ListInstanceAssociations",
      "ssm:PutInventory",
      "ssm:PutComplianceItems",
      "ssm:PutConfigurePackageResult",
      "ssm:UpdateAssociationStatus",
      "ssm:UpdateInstanceAssociationStatus",
      "ssm:UpdateInstanceInformation",
      "ssm:SendCommand",
      "ssm:GetCommandInvocation",
      "ssm:ListCommands",
      "ssm:ListCommandInvocations",
    ]
    resources = ["*"]
  }

  # Canais do SSM agent (Session Manager / Run Command).
  statement {
    sid    = "SsmChannels"
    effect = "Allow"
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel",
      "ec2messages:AcknowledgeMessage",
      "ec2messages:DeleteMessage",
      "ec2messages:FailMessage",
      "ec2messages:GetEndpoint",
      "ec2messages:GetMessages",
      "ec2messages:SendReply",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "S3ProjectBuckets"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.project_name}-*",
      "arn:aws:s3:::${var.project_name}-*/*",
    ]
  }

  statement {
    sid    = "CognitoUserAdmin"
    effect = "Allow"
    actions = [
      "cognito-idp:AdminConfirmSignUp",
      "cognito-idp:ListUsers",
    ]
    resources = [aws_cognito_user_pool.main.arn]
  }

  # Envio de logs dos containers (driver awslogs) aos log groups do projeto.
  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = flatten([
      for grupo in aws_cloudwatch_log_group.containers : [grupo.arn, "${grupo.arn}:*"]
    ])
  }
}

resource "aws_iam_policy" "permissions_boundary" {
  name        = "${local.prefix}-permissions-boundary"
  description = "Teto de permissoes de qualquer role tc3-* (exigida no CreateRole do user do TFC)."
  policy      = data.aws_iam_policy_document.permissions_boundary.json
}

# --- Role da EC2 ---------------------------------------------------------------
data "aws_iam_policy_document" "ec2_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name                 = "${local.prefix}-ec2"
  description          = "Instance profile da EC2 da aplicacao (SSM, ECR pull, SSM params, Cognito)."
  assume_role_policy   = data.aws_iam_policy_document.ec2_trust.json
  permissions_boundary = aws_iam_policy.permissions_boundary.arn
}

# SSM Agent (Run Command / Session Manager) - substitui SSH por completo.
resource "aws_iam_role_policy_attachment" "ec2_ssm_core" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "ec2" {
  # Login no registry (a acao nao suporta restricao por recurso).
  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # Pull somente dos repositorios do projeto.
  statement {
    sid    = "EcrPull"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [for repo in aws_ecr_repository.services : repo.arn]
  }

  # Envs de producao resolvidas em runtime pelo deploy.sh (inclui SecureString).
  statement {
    sid    = "SsmParamsRead"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]
    resources = ["arn:aws:ssm:${var.aws_region}:${local.account_id}:parameter${local.ssm_prefix}/*"]
  }

  # Baixa o compose de producao + deploy.sh publicados pelo workflow.
  statement {
    sid       = "DeployArtifactsRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.deploy_artifacts.arn}/deploy/*"]
  }

  # Chamadas do servico de auth que exigem IAM (SignUp/InitiateAuth/GetUser
  # sao APIs publicas do Cognito): auto-confirmacao de cadastro e resolucao
  # de perfil por sub (ListUsers com filtro, no GET /v1/clientes/{sub}).
  statement {
    sid    = "CognitoUserAdmin"
    effect = "Allow"
    actions = [
      "cognito-idp:AdminConfirmSignUp",
      "cognito-idp:ListUsers",
    ]
    resources = [aws_cognito_user_pool.main.arn]
  }

  # O daemon do Docker (host) envia stdout/stderr dos containers ao CloudWatch
  # Logs via driver awslogs, usando este instance profile. Os grupos ja sao
  # criados pelo Terraform (logs.tf) - sem CreateLogGroup aqui.
  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = flatten([
      for grupo in aws_cloudwatch_log_group.containers : [grupo.arn, "${grupo.arn}:*"]
    ])
  }
}

resource "aws_iam_role_policy" "ec2" {
  name   = "${local.prefix}-ec2"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ec2.json
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${local.prefix}-ec2"
  role = aws_iam_role.ec2.name
}

# --- OIDC provider do GitHub Actions ---------------------------------------------
# Federacao sem segredos de longa duracao: o deploy.yml troca o token OIDC do
# GitHub por credenciais efemeras da role tc3-gha-deploy. Thumbprints publicos
# do GitHub; a AWS valida o emissor de forma gerenciada.
# Condicional (var.criar_oidc_github): o root local desliga porque o floci nao
# suporta CreateOpenIDConnectProvider.
resource "aws_iam_openid_connect_provider" "github" {
  count = var.criar_oidc_github ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
}

# --- Role de deploy do GitHub Actions (OIDC) ------------------------------------
data "aws_iam_policy_document" "gha_deploy_trust" {
  count = var.criar_oidc_github ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github[0].arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Somente a branch main do repo (PRs de forks nao assumem a role).
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_oidc_sub]
    }
  }
}

data "aws_iam_policy_document" "gha_deploy" {
  count = var.criar_oidc_github ? 1 : 0

  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # Push/pull restrito aos dois repositorios do projeto.
  statement {
    sid    = "EcrPushPull"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = [for repo in aws_ecr_repository.services : repo.arn]
  }

  # Publica o compose de producao + deploy.sh consumidos pela EC2.
  statement {
    sid       = "DeployArtifactsWrite"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.deploy_artifacts.arn}/deploy/*"]
  }

  # Descobre a instancia alvo (parametro mantido pelo Terraform).
  statement {
    sid       = "SsmReadInstanceId"
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.instance_id.arn]
  }

  # Run Command: somente o documento AWS-RunShellScript e somente ESTA instancia.
  statement {
    sid     = "SsmSendCommand"
    effect  = "Allow"
    actions = ["ssm:SendCommand"]
    resources = [
      "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript",
      "arn:aws:ec2:${var.aws_region}:${local.account_id}:instance/${aws_instance.app.id}",
    ]
  }

  # Acompanha o resultado do comando (sem suporte a restricao por recurso).
  statement {
    sid       = "SsmCommandStatus"
    effect    = "Allow"
    actions   = ["ssm:GetCommandInvocation"]
    resources = ["*"]
  }
}

resource "aws_iam_role" "gha_deploy" {
  count = var.criar_oidc_github ? 1 : 0

  name                 = "${local.prefix}-gha-deploy"
  description          = "Assumida pelo workflow deploy.yml via OIDC (ECR push + deploy via SSM)."
  assume_role_policy   = data.aws_iam_policy_document.gha_deploy_trust[0].json
  permissions_boundary = aws_iam_policy.permissions_boundary.arn
}

resource "aws_iam_role_policy" "gha_deploy" {
  count = var.criar_oidc_github ? 1 : 0

  name   = "${local.prefix}-gha-deploy"
  role   = aws_iam_role.gha_deploy[0].id
  policy = data.aws_iam_policy_document.gha_deploy[0].json
}
