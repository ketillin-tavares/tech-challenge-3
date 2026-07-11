# Serviço de Vendas

Serviço transacional da plataforma de revenda de veículos (SOAT Fase 3).
Responsável por cadastro e edição de veículos, listagens ordenadas por preço e
pelo **ciclo de compra em duas etapas** — a compra reserva o veículo (venda
`PENDENTE` com prazo) e a **efetivação** confirma o pagamento — por clientes
autenticados, com persistência em PostgreSQL.

O registro/login de clientes vive no [serviço de auth](../auth/) — totalmente
apartado. Este serviço apenas **valida** os access tokens emitidos pelo Cognito,
localmente via JWKS, sem nenhuma chamada ao serviço de auth em runtime.

## Endpoints

| Rota | Auth | Descrição |
|------|------|-----------|
| `POST /v1/veiculos` | grupo `admin` | Cadastra um veículo `DISPONIVEL` (`201`; payload inválido → `422`). |
| `PUT /v1/veiculos/{id}` | grupo `admin` | Edição total — marca, modelo, ano, cor, preço (`404` inexistente, `409` já vendido). |
| `GET /v1/veiculos?status=DISPONIVEL\|VENDIDO&limit=50&offset=0` | pública | Listagem paginada por preço ascendente (`limit` entre 1 e 200). Vendidos incluem `preco_venda`/`data_venda`. |
| `POST /v1/compras` | cliente autenticado | **Inicia** a compra: cria a venda `PENDENTE` e reserva o veículo (`201` com recibo + `expira_em`; `409 VEICULO_INDISPONIVEL` ou `409 RESERVA_ATIVA_EXISTENTE` — máx. 1 reserva ativa por cliente). `cliente_id` = claim `sub` do JWT, nunca do body. |
| `POST /v1/compras/{venda_id}/efetivacao` | dono da venda ou `admin` | **Efetiva** a compra (confirmação do pagamento): venda `PAGA` + veículo `VENDIDO`. Idempotente para vendas já pagas (`200`); `409 TRANSICAO_VENDA_INVALIDA` se cancelada, `409 RESERVA_EXPIRADA` se o prazo venceu (a reserva é liberada), `404` se inexistente ou de outro cliente. |
| `POST /v1/compras/{venda_id}/cancelamento` | dono da venda ou `admin` | Cancela a compra `PENDENTE` e devolve o veículo a `DISPONIVEL`. Idempotente para vendas já canceladas (`200`); `409` se já paga, `404` se inexistente ou de outro cliente. |
| `GET /v1/compras/{venda_id}` | dono da venda ou `admin` | Consulta o estado atual da venda (`404` se inexistente ou de outro cliente). |
| `GET /health` | pública | Liveness probe (sem I/O). |

Documentação interativa (Swagger) em `/docs` com a API no ar.

**Autorização:** o access token do Cognito é validado localmente via JWKS
(assinatura, `iss`, `exp`, `token_use=access`, `client_id`, `cognito:groups`).
Token ausente ou inválido → `401`; usuário sem o grupo `admin` nas rotas
administrativas → `403`.

## Arquitetura

Clean Architecture com Ports & Adapters (convenções em `services-pattern.md`
na raiz do monorepo):

```
src/
├── domain/           # Entidades (Veiculo, Venda), VOs (StatusVeiculo, StatusVenda, Ano,
│                     # Preco, ClienteAutenticado), exceções de domínio, ports de persistência
├── application/      # Use cases (Cadastrar, Editar, IniciarCompra, EfetivarCompra,
│                     # CancelarCompra, ObterCompra, ExpirarReservasVencidas,
│                     # ListarDisponiveis, ListarVendidos) + ports (TokenVerifier, VeiculoQueryService)
├── interface/        # Controllers FastAPI, gateways SQLAlchemy, UnitOfWork, presenters
└── infrastructure/   # Engine async, models ORM, Alembic, cliente JWKS, logging (loguru),
                      # task asyncio de expiração de reservas (lifespan)
```

Os use cases dependem apenas de interfaces abstratas (Ports); a injeção das
implementações concretas (Adapters) acontece na borda, nos controllers.

### Regras de domínio

- **Veiculo** tem ciclo de vida `DISPONIVEL → RESERVADO → VENDIDO`: a compra
  reserva (`reservar()`), a efetivação vende (`marcar_como_vendido()`, única e
  irreversível) e o cancelamento/expiração devolve a `DISPONIVEL`
  (`liberar_reserva()`); edição proibida após a venda.
- **Venda** tem ciclo de vida `PENDENTE → PAGA | CANCELADA` (estados
  terminais), com snapshot do preço no momento da reserva (`preco_venda`) e
  prazo de validade da reserva (`expira_em`, TTL configurável — default 30
  min). `data_venda` só é preenchida na efetivação.
- **Expiração de reserva** em duas defesas: verificação *lazy* na efetivação
  (cancela e libera o veículo na mesma transação do `409 RESERVA_EXPIRADA`) e
  varredura periódica em background (task asyncio no lifespan, com
  `FOR UPDATE SKIP LOCKED`).
- Exceções de domínio são traduzidas para HTTP apenas na camada de interface.
- Transições atômicas via `UnitOfWork` + `SELECT ... FOR UPDATE`; invariantes
  garantidas no banco por **índices únicos parciais**: no máximo 1 venda ativa
  (`PENDENTE`/`PAGA`) por veículo e 1 venda `PENDENTE` por cliente (anti-abuso
  de reservas) — corrida vira `409`. Listagem de vendidos usa JOIN único (sem N+1).

## Stack

- **Python** >= 3.13, dependências gerenciadas exclusivamente com **uv**
- **FastAPI** + **uvicorn** (API), **pydantic**/pydantic-settings (validação e config)
- **SQLAlchemy async** + **asyncpg** (PostgreSQL), **Alembic** (migrations)
- **PyJWT** (validação de token), **loguru** (logging)
- Dev: **pytest** (+ asyncio, cov, testcontainers), **ruff**, **ty**, **httpx**

## Variáveis de ambiente

Lidas por `src/environment.py` (pydantic-settings) a partir do ambiente ou de
um `.env` local. Modelo comentado em [`env.example`](env.example) — copie e
preencha (**nunca versione o `.env`**).

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `DATABASE_URL` | sim | — | DSN async do PostgreSQL (ex.: `postgresql+asyncpg://revenda:revenda@localhost:5432/revenda`). |
| `COGNITO_CLIENT_ID` | sim | — | App Client esperado (validado no claim `client_id`). |
| `COGNITO_ISSUER` | sim | — | Emissor esperado (claim `iss`). |
| `JWKS_URL` | não | `""` | URL do JWKS; se vazio, derivada de `COGNITO_ISSUER` + `/.well-known/jwks.json`. |
| `CORS_ORIGINS` | não | `""` (desligado) | Origens permitidas ao frontend (CSV); vazio não registra o middleware. |
| `CORS_ALLOW_CREDENTIALS` | não | `false` | Credenciais em respostas CORS (proibido combinar com `*`). |
| `COMPRA_RESERVA_TTL_MINUTOS` | não | `30` | Validade da reserva (1 a 1440). |
| `COMPRA_EXPIRACAO_INTERVALO_SEGUNDOS` | não | `60` | Intervalo da varredura de reservas vencidas (10 a 3600). |
| `ENVIRONMENT` | não | `development` | `development` \| `staging` \| `production`. |
| `LOG_LEVEL` | não | `INFO` | `TRACE` \| `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL`. |

## Banco de dados

PostgreSQL com migrations Alembic (`src/infrastructure/alembic/`):

- **`veiculos`** — id (UUID), marca, modelo, cor, ano, preço `Numeric(12,2)`,
  status, timestamps; índice composto `(status, preco)` para as listagens.
- **`vendas`** — id (UUID), `veiculo_id` (FK), `cliente_id` (`sub` opaco do
  JWT), `preco_venda`, `status`, `expira_em`, `data_venda` (nullable),
  timestamps; índices únicos **parciais** `uq_vendas_veiculo_id_ativa`
  (1 venda `PENDENTE`/`PAGA` por veículo) e `uq_vendas_cliente_pendente`
  (1 venda `PENDENTE` por cliente).

```bash
make migrate                       # alembic upgrade head (exige Postgres acessível)
```

Seed de veículos de exemplo (idempotente): `python -m src.seed_veiculos` —
executado automaticamente na stack Docker.

## Como rodar localmente

```bash
cp env.example .env                # preencha COGNITO_CLIENT_ID/COGNITO_ISSUER
make install                       # uv sync
make migrate                       # exige Postgres acessível em DATABASE_URL
uv run uvicorn src.main:app --port 8001 --reload
```

API em `http://localhost:8001` (docs em `/docs`). O alvo `make run` sobe o
uvicorn com `--reload` na porta default do uvicorn (8000); a porta padrão do
serviço na stack é **8001**.

### Via Docker (stack completa)

Na raiz do monorepo:

```bash
docker compose up -d --build
```

Sobe Postgres (rede interna), roda migrations e seed automaticamente e expõe
**vendas em `http://localhost:8001`** e **auth em `http://localhost:8000`**,
além do emulador Cognito local para desenvolvimento. O `Dockerfile` é
multistage (builder + runtime slim), roda como usuário non-root e tem
healthcheck nativo em `/health`.

### Fluxo fim-a-fim

1. `POST http://localhost:8000/v1/auth/register` — cadastra o cliente (email, senha, nome, CPF)
2. `POST http://localhost:8000/v1/auth/login` — obtém o `access_token`
3. `GET  http://localhost:8001/v1/veiculos?status=DISPONIVEL` — lista disponíveis
4. `POST http://localhost:8001/v1/compras` com `Authorization: Bearer <token>` — inicia a compra (venda `PENDENTE`, veículo reservado)
5. `POST http://localhost:8001/v1/compras/{venda_id}/efetivacao` — efetiva a compra (venda `PAGA`, veículo `VENDIDO`)
6. `GET  http://localhost:8001/v1/veiculos?status=VENDIDO` — confirma a venda

## Testes

O serviço possui suíte de testes automatizados em `tests/`. Para executá-la:

```bash
make test          # uv run pytest -m "not integration"
```
