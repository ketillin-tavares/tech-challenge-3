# Infraestrutura AWS e CI/CD

Infra como codigo (Terraform + AWS, state e execucao no **HCP Terraform**) e
pipelines (GitHub Actions) do monorepo. Regiao unica: **us-east-2**. Prefixos:
recursos `tc3-*`, buckets `tech-challenge-3-*`.

## Visao geral

```
infra/
├── stack/       # Modulo compartilhado com TODOS os recursos: VPC/SG, EC2
│                # (docker compose), RDS PostgreSQL, Cognito, ECR, SSM
│                # Parameter Store, OIDC provider do GitHub, roles IAM
├── main/        # Root de PRODUCAO (CLI-driven: o infra.yml dispara, mas
│                # execucao + state ficam no HCP Terraform) -> module ../stack
├── local/       # Root de TESTE local: mesmo stack apontando para o emulador
│                # floci (http://localhost:4566), state local
└── tfc-user-policy.json  # policy do IAM user usado pelo HCP Terraform

deploy/
├── docker-compose.prod.yml  # stack de producao (migrations + vendas + auth)
└── deploy.sh                # executado NA EC2 via SSM Run Command

.github/workflows/
├── quality.yml  # PRs e main: ruff + ty + pytest (cobertura) + SonarCloud (gate)
├── infra.yml    # workflow_dispatch: fmt/validate/plan/apply/destroy (remoto no TFC)
└── deploy.yml   # push na main: build -> ECR -> deploy na EC2 via SSM
```

### Os 3 fluxos CI/CD

| Fluxo | Arquivo | Disparo | Manual? | Onde roda |
|-------|---------|---------|---------|-----------|
| **Qualidade** | quality.yml | PRs + push na main | Nao (automático) | GitHub runner |
| **Infra** | infra.yml | Botão Actions | Sim (sempre) | HCP Terraform (remoto) |
| **Deploy** | deploy.yml | Push na main ou botão | Nao (auto) ou Sim (manual) | GitHub runner + EC2 via SSM |

## Arquitetura de producao

- **EC2 t3.micro** (subnet publica, EIP) roda `docker compose` com as imagens
  do ECR. Sem SSH: administracao e deploy 100% via **SSM** (Session Manager /
  Run Command). SG expoe apenas 8000 (auth) e 8001 (vendas).
- **RDS PostgreSQL db.t3.micro** em subnets privadas (sem rota de internet),
  acessivel somente pelo SG da EC2. Senha gerada pelo Terraform e guardada em
  SSM SecureString (nunca em texto plano no repo).
- **Cognito** gerenciado pelo Terraform: user pool (username = e-mail, senha
  minima 8 alinhada ao dominio), app client sem secret (USER_PASSWORD_AUTH) e
  grupo `admin`.
- **Sem NAT Gateway e sem ALB** (custo): a EC2 sai para a internet pelo IGW; o
  RDS nao precisa de saida.
- **Envs de producao** vivem no **SSM Parameter Store** (`/tc3/prod/*`); a
  cada deploy o `deploy.sh` resolve os parametros na propria instancia e gera
  `/opt/tc3/.env` (0600). Workflows e repo nunca tocam nos valores.
- **Logs centralizados no CloudWatch Logs** (`/tc3/prod/{auth,vendas,
  migrations}`, retencao 14 dias): os containers usam o driver `awslogs` do
  Docker - o loguru continua escrevendo em stdout e o daemon envia ao
  CloudWatch com o instance profile.
- **Identidades**: o `deploy.yml` autentica na AWS via **OIDC** (role
  `tc3-gha-deploy`, restrita a
  `repo:ketillin-tavares/tech-challenge-3:ref:refs/heads/main`); o servico de
  auth usa o **instance profile** da EC2 (IMDSv2). O Terraform usa chaves AWS
  estaticas guardadas como env vars *sensitive* no workspace do HCP Terraform
  (trade-off consciente do projeto; o job de infra no GitHub nao ve essas
  chaves).

## Manual vs Automático

Resposta direta: o que precisa fazer na mao vs o que os Actions fazem sozinhos.

### Setup inicial (UMA vez)

Passos 1-6 abaixo. Feitos uma unica vez quando o projeto ainda nao tem infra.
Depois disso, nenhum deles se repete.

### Primeiro deploy

Disparado via Actions apenas APOS o setup (Passo 7 abaixo). Automatico em si,
mas depende do setup anterior ter terminado (a variable `AWS_DEPLOY_ROLE_ARN`
só existe depois que a infra foi provisionada).

### Atualizacoes de APLICACAO (`services/**`, `deploy/**`)

**ZERO passo manual**. Fluxo automatico:
  1. Abrir PR (commit em branch nova).
  2. `quality.yml` roda checks (ruff + ty + pytest + SonarCloud) como status
     de PR - bloqueante, nada entra sem passar.
  3. Aprovar e mergear na `main` (manual, garantia humana).
  4. `deploy.yml` builda automaticamente, publica no ECR e executa SSM Run
     Command na EC2. Nada a clicar, nada a copiar após o merge.

### Atualizacoes de INFRA (`infra/main/**`, `infra/stack/**`)

**Passo manual obrigatorio no TFC**. Fluxo:
  1. Editar `.tf` num PR, mesma revisão de qualidade normal (quality.yml nao
     roda para arquivos `infra/`, apenas PRs de code).
  2. Mergear na `main`.
  3. **Após o merge**: botão Actions > infra > Run workflow > acao=`plan`.
     Revisar o plano (output no log do job e no TFC workspace > Runs).
  4. Botão Actions > infra > Run workflow > acao=`apply` (mesma branch main).
  5. Aguardar conclusao. Manual por design: mudancas de infraestrutura
     devem ter gate humano (o plano mostra exatamente o que vai mudar).

### Rotacoes periodicas (manuais)

- **Team token do HCP Terraform** (expira em data configurada; ver Passo 2 do
  setup): rotacione na organizacao do TFC antes da expiracao e atualize o
  secret `TF_API_TOKEN` no GitHub.
- **Access key do IAM user** (Passo 3 do setup): rotacione junto com o team
  token. Criar nova, testar, depois deletar a velha. Sem downtime se feito
  antes da expiracao.

---

## Setup inicial passo a passo

### Passo 0: codigo na `main`

Primeiro, garanta que o repositorio foi clonado e o codigo (incluso os
workflows) ja existe na branch `main`. Workflows só aparecem no menu Actions
quando existem na branch default (main). Se ainda nao fez clone:

```bash
git clone https://github.com/ketillin-tavares/tech-challenge-3.git
cd tech-challenge-3
git checkout main
```

### Passo 1: SonarCloud (sonarcloud.io)

1. Acesse <https://sonarcloud.io> e faça login com sua conta GitHub.
2. Crie uma **organizacao** (se não tiver):
   - Menu superior direito > My Organizations > + Create new organization.
   - Nome e chave opcicionais; clique Create.
   - Salve a **Organization Key** (aparece na pagina da org; ex:
     `seu-github-username`). Anotou? Vai usar no Passo 5.
3. Crie **DOIS projetos** (um por servico), ambos na sua organizacao:
   - No topo: Analyze new project > Select repositories > escolha
     `tech-challenge-3` > Set up project.
   - Na proxima tela, escolha **Manually** (CLI, não em UI).
   - **Project key** (algo como `tech-challenge-3-auth`; deve ser unico na
     org) e **Display name** (ex: `tech-challenge-3 - Auth`); click Set up.
   - Copie o **Project key** (aparece em Administration > Projects Management
     ou na URL). **Faca isso para os DOIS projetos** (auth e vendas).
     Anotou ambos? Vai usar no Passo 5.
   - Em cada projeto, vá a **Administration > Analysis Method** e desative
     **Automatic Analysis** (como a qualidade vem do CI, isso evita corridas).
4. Gere um **token de acesso**:
   - Menu superior direito > My Account > Security > Generate Tokens.
   - Nome: algo como `tech-challenge-3-ci`.
   - Type: **User token** ou **Project analysis token** (ambos funcionam; user
     token da acesso a qualquer projeto, project token apenas um).
   - Copie o token. Este é o **SONAR_TOKEN** do Passo 5.

### Passo 2: HCP Terraform (app.terraform.io)

1. Acesse <https://app.terraform.io> e crie uma conta (plano free atende).
   - Confirme o e-mail.
2. Crie uma **organizacao** (conta so, sem necessidade de "org" ainda?):
   - Settings > Organizations (ou direto criar na pagina inicial).
   - Salve o **Organization name** (usado no Passo 5 como
     `TF_CLOUD_ORGANIZATION`).
3. **Ative 2FA** na organizacao (protege o state que tem senhas/tokens):
   - Organization settings > Authentication > Enable 2FA (ou similar).
   - Confirme com seu authenticator (Authy/Google Authenticator).
4. Crie o **workspace** `tech-challenge-3`:
   - Menu (lado esquerdo) > Workspaces > + New > Workspace.
   - Name: `tech-challenge-3`.
   - **Workflow**: escolha **CLI-driven** (nao VCS-driven; você dispara via
     GitHub Actions, nao git push direto).
   - Clique Create. Salve a URL do workspace; vira output.
   - Abra o workspace > Settings > General > verifique **Execution Mode** =
     **Remote** (padrao; o plano e apply rodas nas máquinas do TFC, nao no
     seu PC). Deixe como está.
   - Na MESMA tela (Settings > General), configure **Terraform Working
     Directory** = `infra/main` e salve. OBRIGATORIO neste layout: o root
     referencia o modulo `../stack`; com o working directory setado, o CLI
     detecta que o comando roda dentro de `infra/main`, sobe o repositorio
     inteiro (incluindo `infra/stack/`) e o TFC executa dentro de
     `infra/main`. Sem isso, so a pasta `infra/main` e enviada ao TFC e o
     run remoto falha com "module not found ../stack".
5. Crie um **time** dedicado ao projeto (accesso restrito):
   - Organization settings > Teams (ou Members) > + New team.
   - Name: `tc3-ci` (ou similar).
   - Permissions: conceda **Manage workspaces** (ou Plan & Apply) SOMENTE para
     o workspace `tech-challenge-3`. Sem admin de organizacao.
   - Salve.
6. Gere um **Team token** com data de expiracao:
   - Organization settings > API tokens (ou Teams > tc3-ci > API token).
   - Click Generate > Type: **Team token** (nao user token: seu time token
     limita o raio de um vazamento ao workspace do projeto; user token
     exporia toda a org se vazar).
   - Expiration: defina (ex: 90 dias).
   - Copie o token. Este é o **TF_API_TOKEN** do Passo 5.

### Passo 3: IAM user na AWS (console.aws.amazon.com)

1. Abra o **console AWS** e vá a **IAM** > **Users** > **Create user**.
   - Name: `tc3-terraform` (ou similar).
   - Console access: **nao marque** (este user nunca entra no console, só APIs).
   - Clique Next.
2. **Attach policy**:
   - Selecione **Attach policies directly**.
   - Clique **Create policy** > tab **JSON** > copie todo o conteúdo de
     [`infra/tfc-user-policy.json`](tfc-user-policy.json) do repositorio e
     cole na UI.
   - Policy name: `tc3-terraform-policy` (ou similar).
   - Clique Create.
   - Volte ao formulario de user; selecione a policy que acabou de criar e
     clique Next, depois Create.
3. Gere a **access key**:
   - Abra o user `tc3-terraform` > Security credentials > Create access key.
   - Use case: **Third-party service**.
   - Clique Create.
   - **Copie e GUARDE o Access key ID e Secret access key** (so mostra UMA vez).
     Anotou? Vai usar no Passo 4.

**Sobre a policy**: ela permite ao user Terraform provisionar EC2/RDS/Cognito/ECR/SSM e
criar roles IAM (`tc3-*`), MAS com a constraints `tc3-permissions-boundary`: o user
so consegue criar uma role se a boundary estiver anexada. Sem isso, alguém criaria
uma role `tc3-admin` com policy arbitraria e escala para admin. A boundary e criada
pelo próprio Terraform na primeira execucao.

### Passo 4: variaveis no workspace do TFC

1. Abra o workspace `tech-challenge-3` no TFC.
2. Vá a **Variables**.
3. Adicione **Environment variables** (nao "Terraform variables"):
   - `AWS_ACCESS_KEY_ID`: valor = Access key ID do Passo 3. **Marque sensitive**.
   - `AWS_SECRET_ACCESS_KEY`: valor = Secret access key do Passo 3. **Marque
     sensitive**.
   - `AWS_DEFAULT_REGION`: valor = `us-east-2` (nao marque sensitive).
4. Salve.

### Passo 5: GitHub (Settings > Environments e Secrets/Variables)

1. Abra o repositorio em GitHub > **Settings** > **Environments** > **New
   environment** > name: `infra`.
   - Deployment branches: **Selected branches** > Add > escolha `main`.
   - (Opcional e recomendado) **Required reviewers**: marque para exigir
     aprovacao antes de cada plan/apply - ajuda a evitar typos.
   - Salve.
2. Dentro do environment `infra` > **Environment secrets** > **Add secret**:
   - Name: `TF_API_TOKEN`.
   - Value: Team token gerado no Passo 2. Clique Add secret.
3. Volte a **Settings** > **Secrets and variables** > **Actions** (tab
   **Secrets**):
   - **Secret** `SONAR_TOKEN`: value = token gerado no Passo 1. Add secret.
4. Na mesma tela, tab **Variables** (repository-level, nao environment):
   - **Variable** `TF_CLOUD_ORGANIZATION`: value = organization name do Passo
     2. Add variable.
   - **Variable** `SONAR_ORGANIZATION`: value = Organization Key do Passo 1.
     Add variable.
   - **Variable** `SONAR_PROJECT_KEY_AUTH`: value = Project key do projeto de
     auth criado no Passo 1. Add variable.
   - **Variable** `SONAR_PROJECT_KEY_VENDAS`: value = Project key do projeto de
     vendas criado no Passo 1. Add variable.
   - (A variable `AWS_DEPLOY_ROLE_ARN` ainda nao existe; e criada após o Passo 6.)

### Passo 6: provisionar a infra (primeira vez)

1. Abra o repositorio > **Actions** > **infra** > **Run workflow**:
   - Branch: `main` (ja vem preenchido).
   - acao: `plan`.
   - Clique **Run workflow**.
2. Aguarde o job terminar. Leia o output:
   - **No GitHub**: job > step "Terraform plan" mostra as mudancas.
   - **No TFC**: Organization > Projects & workspaces > `tech-challenge-3` >
     Runs > abra o run mais recente - lê o plano inteiro com mais detalhes.
   - Verifique: cria 1 VPC, 1 EC2, 1 RDS, 1 Cognito pool, ECR, SSM params? Está
     bom.
3. Se o plano ficou OK, rode novamente:
   - **Actions** > **infra** > **Run workflow** > acao: `apply` > **Run
     workflow**.
   - Aguarde. O apply refaz o plano no TFC e aplica em seguida (execucao remota,
     ~2-5 minutos).
   - Verifique no log do job o step **Outputs** - copie o valor de
     `gha_deploy_role_arn` (algo como `arn:aws:iam::123456789:role/tc3-gha-deploy`).
4. Crie a **variable** `AWS_DEPLOY_ROLE_ARN` no GitHub:
   - Settings > Secrets and variables > Actions > tab Variables > + New
     repository variable.
   - Name: `AWS_DEPLOY_ROLE_ARN`.
   - Value: o valor copiado acima.
   - Add variable.
5. **Aguarde ~2 minutos**: a EC2 roda cloud-init (instala Docker, registra no SSM) e
   nao está pronta imediatamente apos o apply.

**TOCTOU (time-of-check-time-of-use)**: entre o plan (Passo 2) e o apply (Passo 3),
o codigo na `main` pode mudar se novos commits entrarem. O TFC refaz o plan sobre
o codigo NOVO no apply - pode resultar em diferenca. Solucao: nao deixe PRs merging
entre plan e apply (required reviewers no environment `infra` ajudam).

**Gate do Cognito (custom attribute `custom:cpf`)**: adicionar o atributo ao
pool existente e ADITIVO (`update in-place`), mas o plan **NUNCA** pode mostrar
`aws_cognito_user_pool.main must be replaced` - replace destroi o pool e todos
os usuarios. Se aparecer, aborte e investigue antes do apply. O bloco `schema`
do `custom:cpf` em `cognito.tf` nao deve ser editado apos criado (alterar/
remover custom attribute forca replace).

**CORS do frontend**: a variavel Terraform `cors_origins` (CSV de origens, ex.
`https://frontend.exemplo.com`) cria o parametro SSM `/tc3/prod/cors/origins`,
que o `deploy.sh` injeta como `CORS_ORIGINS` nos dois servicos. Vazia (default),
o CORS fica desabilitado.

### Passo 7: primeiro deploy

1. **Actions** > **deploy** > **Run workflow**:
   - Branch: `main`.
   - (Sem inputs adicionais.)
   - Clique **Run workflow**.
2. O job:
   - Builda as 2 imagens (auth + vendas, target runtime) com tag SHA do commit.
   - Faz login no ECR e publica.
   - Publica `deploy/docker-compose.prod.yml` e `deploy/deploy.sh` no S3.
   - Roda SSM Run Command na EC2: executa o `deploy.sh`, que baixa os arquivos
     do S3, gera `/opt/tc3/.env` a partir do SSM Parameter Store, faz `docker
     login`, roda migrations, e sobe os containers com `compose up -d`.
3. Aguarde conclusao. Verifique:
   - Job log > step "Acompanha o resultado do deploy" mostra stdout/stderr da
     instancia.
   - Se disser "deploy falhou", leia o erro (pode ser image pull, migrations,
     ou healthcheck).
   - Se "Success", as APIs estao subindo.

### Passo 8: atualizar `.env` locais para o Cognito real

O user pool foi criado pelo Terraform (nao manualmente). Pegue os outputs do
apply do Passo 6 e atualize os `.env` locais:

- `services/auth/.env`:
  - `AWS_REGION=us-east-2`
  - `COGNITO_USER_POOL_ID=<output cognito_user_pool_id do apply>`
  - `COGNITO_CLIENT_ID=<output cognito_client_id do apply>`
  - `AWS_ENDPOINT_URL=` (vazio, aponta para a AWS real, não emulador)
  - `AWS_ACCESS_KEY_ID=<suas chaves AWS pessoais para dev local>`
  - `AWS_SECRET_ACCESS_KEY=<suas chaves AWS pessoais para dev local>`

- `services/vendas/.env`:
  - `COGNITO_CLIENT_ID=<output cognito_client_id do apply>`
  - `COGNITO_ISSUER=<output cognito_issuer do apply>`
  - `JWKS_URL=` (vazio, derivado do issuer automaticamente)

Depois, apague o user pool manual antigo no console AWS (se criou um antes) para
nao confundir e nao pagar.

---

## Como conferir que esta tudo de pe

Apos o Passo 7 (primeiro deploy), rode estas verificacoes:

### Health check das APIs

```bash
# Pegue o IP publico da EC2 nos outputs do apply do Passo 6:
# No log do job ou no TFC > workspace > Outputs (chave: auth_url / vendas_url)
APP_IP="<public_ip>"

# Health check de ambas as APIs
curl http://${APP_IP}:8000/health
curl http://${APP_IP}:8001/health

# Se responderem com status 200, estão vivas.
```

### Fluxo E2E com curl

Adapte do README raiz (Fluxo fim-a-fim) substituindo `localhost` pelo IP:

```bash
APP_IP="<public_ip>"

# 1. Registrar comprador
curl -X POST http://${APP_IP}:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"comprador@test.com","password":"SenhaForte123"}'

# 2. Login
TOKEN=$(curl -s -X POST http://${APP_IP}:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"comprador@test.com","password":"SenhaForte123"}' \
  | jq -r '.access_token')

# 3. Listar veiculos disponiveis
curl http://${APP_IP}:8001/v1/veiculos?status=DISPONIVEL \
  -H "Authorization: Bearer ${TOKEN}"

# 4. Comprar (copie um veiculo_id da lista acima)
curl -X POST http://${APP_IP}:8001/v1/compras \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"veiculo_id":"<veiculo_id>","quantidade":1}'

# 5. Verificar veiculo marcado como vendido
curl http://${APP_IP}:8001/v1/veiculos?status=VENDIDO \
  -H "Authorization: Bearer ${TOKEN}"
```

### Promover um usuario a admin

As rotas de gestao de veiculos (`POST/PUT /v1/veiculos`) exigem o grupo
`admin` no token. O Terraform cria o grupo no Cognito, mas **nao ha
provisionamento automatico de membros**: tornar um usuario admin e um passo
manual no console AWS.

1. Registre o usuario normalmente (`POST /v1/auth/register`).
2. AWS console > Cognito > User pools > pool `tc3-users` > Users > clique no
   usuario > Group memberships > **Add user to group** > selecione `admin`.
3. Faca **login novamente** (`POST /v1/auth/login`): o grupo so entra na claim
   `cognito:groups` de tokens emitidos apos a associacao — tokens antigos
   continuam sem o grupo ate expirar.

### Logs do deploy e da instancia

- **CloudWatch Logs (centralizado, sem entrar na instancia)**: cada container
  envia stdout/stderr para um log group proprio via driver `awslogs` do Docker
  (o daemon usa o instance profile `tc3-ec2`; grupos criados pelo Terraform em
  `infra/stack/logs.tf`, retencao padrao de 14 dias):
  - AWS console > CloudWatch > Log groups > `/tc3/prod/auth`,
    `/tc3/prod/vendas` e `/tc3/prod/migrations`.
  - Ou via CLI: `aws logs tail /tc3/prod/vendas --follow --region us-east-2`.
  - Modo `non-blocking`: indisponibilidade do CloudWatch nao trava as APIs
    (logs podem ser descartados se o buffer de 4 MB encher - trade-off
    consciente).
- **Deploy**: no GitHub, Actions > deploy > job > step "Acompanha o resultado
  do deploy" tem stdout/stderr da EC2.
- **Instancia em tempo real** (sem SSH):
  - AWS console > Systems Manager > Session Manager > Start session > escolha a
    instancia `tc3-*` > Connect.
  - Roda shell interativa na instancia (e auditado no CloudTrail, sem chave SSH).
  - Comandos úteis:
    ```bash
    cd /opt/tc3 && docker compose ps    # status dos containers
    docker compose logs vendas          # logs do serviço
    aws ssm get-parameter --name /tc3/prod/database/url --with-decryption  # ver DSN (cuidado: pode ter senha)
    ```

### SonarCloud dashboards

Apos o primeiro push na `main` (que dispara quality.yml):
- Vá a <https://sonarcloud.io> > seus projetos (`tech-challenge-3-auth` e
  `tech-challenge-3-vendas`).
- Verifique: Coverage % > 0, nenhum blocker bugs, quality gate PASSED.
- Se FAILED, o que deu errado? Quality.yml teria falhado; verifique no GitHub
  Actions.

### Quality como check obrigatorio (branch protection)

Recomendado para garantir que toda mudanca passa por CI/CD:
- Settings > Branches > + Add rule > Branch name pattern: `main`.
- Require status checks to pass before merging > selecione SOMENTE os checks
  dos JOBS do quality.yml:
  - `quality / auth (lint + types + testes + sonar)`
  - `quality / vendas (lint + types + testes + integracao + sonar)`
- Salve. Agora nenhum PR mergeia sem passar em quality.

Como funciona com o path filter: num PR que nao toca um servico, o job dele e
PULADO (`if:` do job) - e job pulado CONTA como aprovado na branch protection.
Ou seja, um PR so de README mergeia sem esperar nada, e um PR que toca um
servico so mergeia se o job (incluindo o gate do Sonar, que falha o job via
`-Dsonar.qualitygate.wait=true`) passar.

**NAO marque como required os checks `[...] SonarCloud Code Analysis`** (vem
do GitHub App do SonarCloud, nao do workflow): eles so reportam quando uma
analise roda no PR - num PR sem mudanca de servico ficam "Expected / waiting"
PARA SEMPRE e travam o merge. O gate do Sonar ja e imposto dentro do job.

---

## Operacao continua

1. **Mudancas de codigo** (`services/**`, `deploy/**`):
   - Branch nova > commit > PR.
   - Quality.yml roda checks (status no PR).
   - Aprova > mergea na `main`.
   - Deploy.yml roda automaticamente; em alguns minutos a mudanca esta em
     producao.
   - Sem clicks adicionais; sem copiar valores.

2. **Mudancas de infra** (`infra/**`):
   - Branch nova > edita `.tf` > PR.
   - Mergea na `main`.
   - **Após merge**: Actions > infra > Run workflow > acao=plan > revisa.
   - Run workflow > acao=apply > aguarda (2-5 min).
   - Manual por design: assegura review humano de mudancas de infraestrutura.

3. **Monitoramento rotineiro**:
   - AWS console > EC2 > instancias (status "running"?).
   - AWS console > RDS > instances (status "available"?).
   - SonarCloud > seus 2 projetos (quality gate PASSED?).
   - GitHub Actions > quality + deploy (sem falhas recentes?).

---

## Destroy

### Via CI/CD (caminho principal)

```
Actions > infra > Run workflow
  acao = destroy
  confirmacao = "destroy"   (campo de texto; protecao contra clique errado)
  Run workflow
```

Aguarde. O destroy roda no TFC (execucao remota, mesma autorizacao e credenciais
do apply). Ele:
- Deleta a EC2, RDS, Cognito pool, ECR, VPC, tudo de uma vez.
- Limpa o state no TFC.
- Aviso: **todos os dados (DB, Cognito users) sao perdidos permanentemente**.

Apos conclusao, a infrastructure esta morta e nao gasta mais.

### Alternativa local (com token do TFC)

Se preferir destruir de um PC (requer `terraform` instalado e acesso ao token):

```bash
cd infra/main

# Autentique no TFC (se nao tiver feito ainda):
terraform login
  # Ou exporte: export TF_TOKEN_app_terraform_io="seu-team-token-do-TFC"

export TF_CLOUD_ORGANIZATION="sua-org-aqui"
export TF_WORKSPACE="tech-challenge-3"

terraform init
terraform destroy
```

**Confira org/workspace antes do init**: um typo faz o init criar um workspace
novo vazio; o destroy vira no-op e a infra real continua de pe (e custando).

---

## Decisoes tecnicas (resumo)

- **EC2 unica com Docker Compose** (em vez de ECS/Fargate ou EKS): decisao
  consciente por custo (~US$ 23/mes). E um ponto unico de falha, sem
  redundancia/auto-scaling, e rollback = re-executar o deploy com o SHA
  anterior. Trade-off completo em
  [docs/adrs/0001-ec2-unica-com-docker-compose.md](../docs/adrs/0001-ec2-unica-com-docker-compose.md).
- **HCP Terraform CLI-driven**: state remoto, lock e historico de runs sem
  bucket/DynamoDB proprios; o infra.yml continua sendo o unico ponto de
  provisionamento. Organizacao/workspace via env vars `TF_CLOUD_ORGANIZATION`
  e `TF_WORKSPACE` (Terraform >= 1.6) em vez de chumbados no `cloud {}`: a org
  ainda nao existia e assim nao ha placeholder quebrado no repo.
- **Chaves AWS estaticas no workspace do TFC** (env vars sensitive): trade-off
  consciente do projeto (simplicidade > OIDC dinamico do TFC). O job de infra
  no GitHub nao possui nenhuma credencial AWS.
- **Permissions boundary `tc3-permissions-boundary`**: o IAM user do TFC so
  cria roles `tc3-*` com a boundary anexada (condicao no `iam:CreateRole` da
  `tfc-user-policy.json`). Sem isso, escopo por prefixo seria escalavel a
  admin (bastaria criar uma role `tc3-x` com policy arbitraria).
- **Deploy por SSM Run Command, sem SSH**: porta 22 fechada, auditoria no
  CloudTrail, e a role de deploy so consegue rodar `AWS-RunShellScript` nesta
  instancia especifica.
- **Instance id via SSM parameter** (`/tc3/prod/ec2/instance_id`): o workflow
  de deploy descobre a instancia sozinho; recriar a EC2 nao quebra o pipeline.
- **Artefatos de deploy via S3**: o compose/script versionados no repo sao
  publicados no bucket e baixados pela instancia (comando SSM pequeno e
  auditavel).
- **Um projeto SonarCloud por servico**: gates e cobertura independentes; um
  servico nao mascara divida do outro (padrao de monorepo do SonarCloud).
- **t3.micro x86_64** (nao t4g/ARM): build nativo nos runners ubuntu, sem
  emulacao QEMU no CI.
- **Politica de senha do Cognito = minimo 8, sem classes obrigatorias**:
  espelha o value object `Senha` do dominio; politica mais rigida no pool
  causaria `InvalidPasswordException` nao mapeada (HTTP 500).
- **IMDSv2 com hop limit 1 + auth em host network**: containers em bridge
  (vendas/migrations, expostos na internet) NAO alcancam o IMDS - uma SSRF
  neles nao rouba credenciais do instance profile. So o auth usa o IMDS
  (boto3 -> Cognito) e por isso roda com `network_mode: host` em producao.
- **Actions pinadas por SHA + dependabot**: workflows com `id-token: write`
  nao seguem tags moveis (supply chain); apenas actions oficiais dos
  fornecedores (actions/, aws-actions/, hashicorp/, astral-sh/, SonarSource/).

## Postura no HCP Terraform

- **2FA obrigatorio** na organizacao (o state contem a senha do RDS e os
  valores dos parametros SSM).
- **Workspace fechado**: sem *global remote state sharing*; acesso restrito ao
  time dedicado do Passo 2 (plan/apply, sem admin de org).
- **Versoes antigas do state retem segredos antigos**: ao rotacionar a senha
  do RDS, lembre que as versoes anteriores do state (visiveis no TFC) ainda
  guardam a senha antiga - conclua a rotacao no banco, nao apenas no state.

## Custos (estimativa mensal)

t3.micro (~US$ 7,5) + db.t3.micro (~US$ 12) + gp3 16+20 GiB (~US$ 3) +
EIP anexado (gratis) + ECR/S3/SSM (centavos) ~= **US$ 23/mes**.
HCP Terraform: plano free (ate 500 recursos gerenciados).

---

## Teste local com emulador

Para testar o stack Terraform ANTES de gastar AWS real, use o emulador
**floci** em `infra/local`. Ver [infra/local/README.md](local/README.md).
