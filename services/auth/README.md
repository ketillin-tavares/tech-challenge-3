# Serviço de Auth

Serviço de **registro e autenticação de compradores** da plataforma de revenda
de veículos (SOAT Fase 3). É totalmente apartado do serviço de vendas, conforme
o requisito do challenge: os dados de clientes vivem **apenas no AWS Cognito** —
este serviço é stateless e não possui banco de dados próprio (sem ORM, sem
migrações).

## Endpoints

| Método | Rota                 | Descrição                                                                                              | Sucesso | Erro |
|--------|----------------------|--------------------------------------------------------------------------------------------------------|---------|------|
| `POST` | `/v1/auth/register`  | Registra um cliente no Cognito com perfil completo — email, senha, nome e CPF (`SignUp` + `AdminConfirmSignUp` — auto-confirmado, sem etapa de e-mail) | `201`   | `409 DADOS_JA_CADASTRADOS` (genérico, anti-enumeração), `422` CPF/email inválido, `429` rate limit |
| `POST` | `/v1/auth/login`     | Autentica o cliente (`InitiateAuth`, fluxo `USER_PASSWORD_AUTH`)                                         | `200`   | `401` credenciais inválidas, `429` rate limit |
| `GET`  | `/v1/clientes/me`    | Perfil do próprio cliente via `GetUser` com o access token (CPF **mascarado**)                           | `200`   | `401` token inválido, `429` |
| `GET`  | `/v1/clientes/{sub}` | Perfil de um cliente pelo `sub` via `ListUsers` — responde "quem comprou?" a partir do `cliente_id` da venda (CPF completo) | `200`   | `401`, `403` sem grupo `admin`, `404`, `429` |
| `GET`  | `/health`            | Liveness probe (`{"status": "ok"}`)                                                                      | `200`   | —    |

Endpoints públicos e de perfil são **rate-limited por IP** (slowapi; ver
variáveis `RATELIMIT_*`). O perfil do cliente (nome, CPF) vive **apenas no
Cognito** (atributo padrão `name` + `custom:cpf`) — decisão registrada na
[ADR 0002](../../docs/adrs/0002-perfil-cliente-cognito-only.md).

Documentação interativa: `http://localhost:8000/docs` (Swagger) e `/redoc`.

### Exemplos

Registro — request `{email, senha, nome, cpf}`, response
`{sub, nome, cpf_mascarado}` (o CPF aceita qualquer formatação e é
normalizado para dígitos):

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@example.com", "senha": "senhaSegura123", "nome": "Usuario Exemplo", "cpf": "123.456.789-09"}'
```

Login — request `{email, senha}`, response com os tokens emitidos pelo Cognito
(`id_token`, `access_token`, `refresh_token`, `token_type`, `expires_in`):

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@example.com", "senha": "senhaSegura123"}'
```

O **access token** retornado é o que o serviço de vendas valida (via JWKS do
Cognito) para autorizar compras e rotas de gestão — não há nenhuma chamada em
runtime entre os dois serviços; o Cognito é o ponto de integração compartilhado.

## Arquitetura

Clean Architecture com Ports & Adapters (ver `services-pattern.md` na raiz do
monorepo):

```
src/
├── domain/               # Regras de negócio puras (apenas pydantic)
│   ├── value_objects/    #   Email, Senha, Cpf (dígitos verificadores + normalização), ClienteAutenticado
│   └── exceptions/       #   DomainError, CredenciaisInvalidasError, ClienteJaExisteError, ClienteNaoEncontradoError, TokenInvalidoError
├── application/          # Regras da aplicação
│   ├── ports/            #   IdentityProvider e TokenVerifier (ABCs)
│   ├── use_cases/        #   RegistrarCliente, AutenticarCliente, ObterPerfilProprio, ObterPerfilPorSub
│   └── dtos/             #   Schemas de entrada/saída (pydantic)
├── interface/            # Adaptadores de borda
│   ├── controllers/      #   Routers FastAPI (v1/auth, v1/clientes, health) + wiring via Depends + rate limit (slowapi)
│   ├── gateways/         #   CognitoIdentityProvider (implementa o port com boto3)
│   └── presenters/       #   Envelope de erro das respostas HTTP + mascaramento de CPF
├── infrastructure/       # Detalhes: fábrica do cliente boto3, validação de JWT via JWKS (PyJWT) e logging (loguru)
├── environment.py        # Settings via pydantic-settings (lê env vars / .env)
└── main.py               # Composition root: cria o FastAPI, registra routers e exception handlers
```

**Política de PII (CPF):** o CPF nunca aparece em logs nem em mensagens de
exceção (mensagens fixas); nas respostas, retorna **mascarado**
(`123.***.***-09`) no eco do registro e no `/me`, e completo apenas no
endpoint administrativo (justificado pela documentação da venda).

O Cognito é um *driven adapter* atrás do port `IdentityProvider` — trocar de
provedor de identidade afeta somente o gateway. As exceções de domínio são
traduzidas para status HTTP exclusivamente na camada de interface.

## Variáveis de ambiente

Carregadas por `pydantic-settings` (`src/environment.py`), com `.env` como
fallback. Template em `env.example`:

| Variável                | Obrigatória | Default        | Descrição |
|-------------------------|-------------|----------------|-----------|
| `AWS_ACCESS_KEY_ID`     | Sim         | —              | Credencial AWS (IAM) com permissão no Cognito |
| `AWS_SECRET_ACCESS_KEY` | Sim         | —              | Credencial AWS (IAM) |
| `COGNITO_USER_POOL_ID`  | Sim         | —              | ID do User Pool do Cognito |
| `COGNITO_CLIENT_ID`     | Sim         | —              | ID do App Client do Cognito |
| `AWS_REGION`            | Não         | `us-east-1`    | Região AWS do User Pool |
| `AWS_ENDPOINT_URL`      | Não         | `""` (AWS real)| Endpoint customizado para emulador local |
| `COGNITO_ISSUER`        | Não         | derivado       | Issuer esperado dos JWTs; vazio = derivado de região + pool |
| `JWKS_URL`              | Não         | derivado       | JWKS do pool; vazio = derivado do issuer |
| `CORS_ORIGINS`          | Não         | `""` (desligado)| Origens permitidas ao frontend (CSV); vazio não registra o middleware |
| `CORS_ALLOW_CREDENTIALS`| Não         | `false`        | Credenciais em respostas CORS (proibido combinar com `*`) |
| `RATELIMIT_ENABLED`     | Não         | `true`         | Liga/desliga o rate limiting (por IP, por processo) |
| `RATELIMIT_REGISTER`    | Não         | `5/minute`     | Limite do register |
| `RATELIMIT_LOGIN`       | Não         | `10/minute`    | Limite do login |
| `RATELIMIT_CLIENTES`    | Não         | `30/minute`    | Limite de `/v1/clientes/*` (protege a quota do Cognito) |
| `ENVIRONMENT`           | Não         | `development`  | `development`, `staging` ou `production` |
| `LOG_LEVEL`             | Não         | `INFO`         | `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

## Como rodar localmente

Pré-requisito: [`uv`](https://docs.astral.sh/uv/) instalado.

```bash
cp env.example .env   # preencha COGNITO_* e credenciais AWS
make install          # uv sync
make run              # API em http://localhost:8000 (uvicorn com --reload)
```

Sem Makefile, o equivalente direto:

```bash
uv sync
uv run uvicorn src.main:app --port 8000 --reload
```

### Via Docker

O `Dockerfile` é multistage: um estágio *builder* instala as dependências com
`uv sync --frozen --no-dev` e o estágio *runtime* (`python:3.13-slim`) copia
apenas a `.venv` e o `src/`, roda como usuário non-root e traz `HEALTHCHECK`
nativo em Python apontando para `/health`. A porta exposta é a `8000`.

Pela raiz do monorepo (sobe a stack completa — auth, vendas, postgres e o
emulador AWS local):

```bash
docker compose up -d --build   # auth em http://localhost:8000
```

No compose, o serviço roda com filesystem read-only, `cap_drop: ALL`,
`no-new-privileges` e limites de CPU/memória, apenas na rede `frontend`
(sem acesso ao postgres).

## Testes

O serviço possui suíte de testes automatizados em `tests/`. Para rodar:

```bash
make test        # ou: uv run pytest
```

As variáveis de ambiente dos testes são mockadas automaticamente pelo
`tests/conftest.py` — nenhum `export` é necessário e nenhuma AWS real é
acessada.

## Qualidade de código

```bash
make quality   # format + lint (ruff) + typecheck (ty) + testes com cobertura
make ci        # paridade com o pipeline (só verifica, não modifica arquivos)
```
