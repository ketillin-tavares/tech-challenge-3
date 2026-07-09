# Teste local com emulador (floci)

O root `infra/local` aplica o **MESMO stack de producao** (modulo
`infra/stack`) no [floci](https://floci.io) (emulador AWS local, drop-in do
LocalStack) - valida todo o provisionamento antes de gastar AWS real. O state e
local (`terraform.tfstate` nesta pasta, ignorado no git) e os endpoints sao
chumbados em `http://localhost:4566`: nada alcanca a AWS de verdade.

## O que é e por que

- **Stack identico**: mesma VPC, EC2, RDS PostgreSQL, Cognito, ECR, SSM que em
  producao.
- **Sem gastar**: emulador local nao fatura nada.
- **Antes de commitar**: valida mudancas de Terraform sem risco.
- **State local**: terraform.tfstate fica em `infra/local/` (ignorado no git),
  nunca se mistura com state de producao do HCP Terraform.

## Como rodar

### 1. Suba o emulador floci

Na raiz do repositorio:

```bash
docker compose up -d floci
```

Aguarde ~10s para o container estar pronto (inicia os servicos AWS).

### 2. Aplique o Terraform

```bash
cd infra/local

terraform init

terraform apply
  # Digite "yes" quando pedir confirmacao
  # Aguarde ~1-2 minutos (cria VPC, EC2, RDS, Cognito, ECR, SSM, etc.)
```

Apos a conclusao, o output mostra o resultado (IPs da EC2, endpoints, etc.).

### 3. Inspecione com AWS CLI

Aponte o AWS CLI para o emulador:

```bash
# Exemplo: listar user pools de Cognito
aws --endpoint-url http://localhost:4566 cognito-idp list-user-pools --max-results 10

# ECR repositories
aws --endpoint-url http://localhost:4566 ecr describe-repositories

# SSM parameters
aws --endpoint-url http://localhost:4566 ssm get-parameter \
  --name /tc3/prod/cognito/client_id --query Parameter.Value --output text

# RDS instances (sim, realmente rodando via containers/Postgres)
aws --endpoint-url http://localhost:4566 rds describe-db-instances
```

### 4. Limpeza

Quando terminar os testes:

```bash
# Destrua o Terraform
terraform destroy
  # Digite "yes" para confirmar

# Desliga o emulador
docker compose stop floci

# Opcional: limpe o estado local
rm -f terraform.tfstate terraform.tfstate.backup .terraform.lock.hcl
```

O container floci persiste dados em `./data` (mesmo que seja descartavel). Se
quiser limpar TUDO:

```bash
docker compose down -v floci   # remove volumes
```

---

## Limitacoes do emulador e contornos

O floci emula AWS, mas nao 100% - alguns servicos tem limitacoes. Este projeto
aplica **contornos** SOMENTE no root local (producao usa defaults sem mudanca).

### criar_oidc_github = false

**Problema**: floci nao implementa `CreateOpenIDConnectProvider` (operacao de
IAM necessaria para OIDC do GitHub).

**Contorno**: em `infra/local/main.tf`, o modulo stack e chamado com
`criar_oidc_github = false`. Resultado:
  - OIDC provider NAO e criado (sem erro).
  - Role `tc3-gha-deploy` NAO e criada (depende do OIDC).
  - Output `gha_deploy_role_arn` fica null.
  - Deploy via GitHub Actions nao e testado aqui (faria AWS real). Deploy test
    pode ser feito em staging/producao.

**Efeito**: nao afeta o resto (VPC, EC2, RDS, Cognito, etc.). Se quiser testar
OIDC, so em producao com AWS real.

### rds_em_vpc = false

**Problema**: RDS do floci nao enxerga as subnets/security groups da VPC
emulada. Erro: `InvalidSubnet` ao tentar criar a instancia dentro da VPC.

**Contorno**: em `infra/local/main.tf`, `rds_em_vpc = false`. Resultado:
  - RDS sobe FORA da VPC (como standalone).
  - Postgres roda normalmente (container real + Postgres real do floci).
  - EC2 ainda consegue acessar via endpoint do RDS (localhost:5432 ou similar).
  - SG nao se aplica (ja que nao tem subnets de VPC).

**Efeito**: configuracao diferente de producao, mas funcional para testes de
database/migrations.

### s3control com localhost.localstack.cloud

**Problema**: provider AWS v6 usa `s3control` (servico distinto de `s3`) para
ler tags de buckets. O SDK prefixa o account ID no hostname (ex:
`000000000000.s3control.us-east-2.amazonaws.com`). No emulador com localhost,
isso vira `000000000000.localhost`, que nao resolve.

**Contorno**: em `infra/local/main.tf`, o endpoint de s3control aponta para
`localhost.localstack.cloud:4566` (DNS publico wildcard do floci que resolve
`*.localhost.localstack.cloud` para 127.0.0.1). Assim `000000000000.localhost.localstack.cloud`
resolve.

**Efeito**: S3 funciona normalmente (buckets criados, objetos, etc.).

### Sem default_tags

**Problema**: IAM do floci nao suporta `TagInstanceProfile` - a operacao que
aplica tags default a instancia profiles falha.

**Contorno**: em `infra/local/main.tf`, provider AWS tem `ignore_tags` (nao
aplica default_tags no emulador). Producao usa default_tags normalmente.

**Efeito**: instancias criadas no teste local nao tem tags Project/ManagedBy.
Nada de funcional quebra; e apenas metadata. Em producao todas tem tags.

---

## Rodando os SERVICOS contra Cognito emulado

Apos o `terraform apply` em `infra/local`, voce tem um Cognito pool, EC2, RDS
rodando no emulador. Os servicos (`services/auth` e `services/vendas`) podem se
conectar a eles. Aqui estao as duas formas:

### Opcao 1: Servicos no HOST (make run)

Executar `make run` na raiz ou nos servicos individuais (ex: `make -C
services/auth run`). Os servicos rodam na sua maquina, nao em containers.

**Arquivo**: `services/auth/.env`

```
AWS_REGION=us-east-2
# Endpoints do emulador local
AWS_ENDPOINT_URL=http://localhost:4566
# Credenciais dummy (emulador nao valida)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
# Valores vindo do output do terraform apply em infra/local
COGNITO_USER_POOL_ID=<output: cognito_user_pool_id>
COGNITO_CLIENT_ID=<output: cognito_client_id>
```

**Arquivo**: `services/vendas/.env`

```
COGNITO_CLIENT_ID=<output: cognito_client_id>
# Issuer do emulador - IMPORTANTE: floci devolve iss = http://localhost:4566/<pool_id> nos tokens
COGNITO_ISSUER=http://localhost:4566/<cognito_user_pool_id>
# JWKS_URL pode ficar vazio (derivado do issuer) ou explicitamente:
JWKS_URL=http://localhost:4566/<cognito_user_pool_id>/.well-known/jwks.json
```

**Comando**:

```bash
cd services/auth
make run     # inicia o servico na porta 8000

# Em outro terminal:
cd services/vendas
make run     # inicia o servico na porta 8001
```

Pronto: auth e vendas conversam com Cognito/RDS do emulador. Teste as APIs
normalmente (curl ou Swagger em `http://localhost:8000/docs`).

### Opcao 2: Servicos no COMPOSE (docker compose up)

Rodar os servicos em containers (junto com Postgres). Use o `docker-compose.yml`
da raiz (que ja define os servicos locais) ou ajuste conforme necessario.

**Arquivo**: `services/auth/.env`

```
AWS_REGION=us-east-2
# No compose, o emulador floci esta na rede `frontend` com hostname `floci`
AWS_ENDPOINT_URL=http://floci:4566
# Credenciais dummy
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
# Valores vindo do terraform apply
COGNITO_USER_POOL_ID=<output: cognito_user_pool_id>
COGNITO_CLIENT_ID=<output: cognito_client_id>
```

**Arquivo**: `services/vendas/.env`

```
COGNITO_CLIENT_ID=<output: cognito_client_id>
# Issuer local - TEM QUE BATER com o "iss" do token do Cognito emulado
COGNITO_ISSUER=http://localhost:4566/<cognito_user_pool_id>
# JWKS_URL: precisa de OVERRIDE para apontar para o floci (containers na rede do compose)
JWKS_URL=http://floci:4566/<cognito_user_pool_id>/.well-known/jwks.json
```

**Comando**:

```bash
# Suba tudo (postgres + auth + vendas + migrations)
docker compose up -d --build

# APIs:
#   auth:   http://localhost:8000/docs
#   vendas: http://localhost:8001/docs

# Para verificar logs:
docker compose logs auth    # logs do auth
docker compose logs vendas  # logs do vendas

# Para parar:
docker compose down
```

**Por que precisa de JWKS_URL override no compose?**: quando vendas (em container
na rede `frontend`) faz uma chamada HTTP para o issuer do Cognito, ele usa
`COGNITO_ISSUER` (que e `http://localhost:4566/<pool_id>`). Mas dentro de um
container, `localhost` e a propria container, nao o host. Entao vendas precisa
buscar as JWKS via `http://floci:4566` (que e como se chama o emulador de DENTRO
da rede compose).

**Nota sobre boto3 e emulador**: ambos os modos exigem credenciais dummy nas
env vars (`AWS_ACCESS_KEY_ID=test`, `AWS_SECRET_ACCESS_KEY=test`) porque o
boto3 (usado internamente por ambos os servicos para Cognito/SSM) passa por
uma cadeia de autenticacao mesmo apontando para um emulador. O emulador nao
valida, mas exige que as chaves existam. **NUNCA use chaves reais apontando
para localhost** (so desperdício, nao funciona mesmo).

---

## Nota final

Se algum recurso falhar SOMENTE no emulador, e limitacao do floci - **nao altere
o stack real** (`infra/stack`) porque uma limitacao de teste. Ao inves:
  - Documente a limitacao neste README (como as 4 acima).
  - Aplique o contorno SOMENTE no root local (variaveis, condicoes, etc.).
  - Teste em staging/producao com AWS real.

Exemplo pratico: se inventarem um novo recurso que o floci nao suporta, criamos
uma variavel `habilitar_novo_recurso = true` no modulo, passamos `false` do
root local, e producao usa `true` (default).
