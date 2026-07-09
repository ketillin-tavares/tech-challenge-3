# Serviço de Auth

Serviço de **registro e autenticação de compradores** da plataforma de revenda
de veículos (SOAT Fase 3). É totalmente apartado do serviço de vendas, conforme
o requisito do challenge: os dados de clientes vivem **apenas no AWS Cognito** —
este serviço é stateless e não possui banco de dados próprio (sem ORM, sem
migrações).

## Endpoints

| Método | Rota                 | Descrição                                                                                              | Sucesso | Erro |
|--------|----------------------|--------------------------------------------------------------------------------------------------------|---------|------|
| `POST` | `/v1/auth/register`  | Registra um cliente no Cognito (`SignUp` + `AdminConfirmSignUp` — auto-confirmado, sem etapa de e-mail) | `201`   | `409` se o e-mail já existe |
| `POST` | `/v1/auth/login`     | Autentica o cliente (`InitiateAuth`, fluxo `USER_PASSWORD_AUTH`)                                         | `200`   | `401` credenciais inválidas |
| `GET`  | `/health`            | Liveness probe (`{"status": "ok"}`)                                                                      | `200`   | —    |

Documentação interativa: `http://localhost:8000/docs` (Swagger) e `/redoc`.

### Exemplos

Registro — request `{email, senha}`, response `{sub}`:

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@example.com", "senha": "senhaSegura123"}'
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
│   ├── value_objects/    #   Email (EmailStr) e Senha (mínimo 8 caracteres)
│   └── exceptions/       #   DomainError, CredenciaisInvalidasError, ClienteJaExisteError
├── application/          # Regras da aplicação
│   ├── ports/            #   IdentityProvider (ABC — contrato do provedor de identidade)
│   ├── use_cases/        #   RegistrarCliente, AutenticarCliente
│   └── dtos/             #   Schemas de entrada/saída (pydantic)
├── interface/            # Adaptadores de borda
│   ├── controllers/      #   Routers FastAPI (v1/auth, health) + wiring via Depends
│   ├── gateways/         #   CognitoIdentityProvider (implementa o port com boto3)
│   └── presenters/       #   Envelope de erro das respostas HTTP
├── infrastructure/       # Detalhes: fábrica do cliente boto3 (cognito-idp) e logging (loguru)
├── environment.py        # Settings via pydantic-settings (lê env vars / .env)
└── main.py               # Composition root: cria o FastAPI, registra routers e exception handlers
```

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
