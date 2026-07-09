# Plataforma de Revenda de Veículos — Tech Challenge SOAT (Fase 3)

| Auth | Vendas |
|------|--------|
| [![Quality gate — Auth](https://sonarcloud.io/api/project_badges/quality_gate?project=tech-challenge-3-auth)](https://sonarcloud.io/summary/new_code?id=tech-challenge-3-auth) | [![Quality gate — Vendas](https://sonarcloud.io/api/project_badges/quality_gate?project=tech-challenge-3-vendas)](https://sonarcloud.io/summary/new_code?id=tech-challenge-3-vendas) |

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## Sobre o Projeto / Tech Challenge

Este repositório contém a solução do **Tech Challenge da Fase 3 da Pós-Tech
SOAT (FIAP)**: uma plataforma de revenda de veículos automotores que funciona
na internet. A entrega é a **API da plataforma**, que será posteriormente
integrada pelo time de frontend.

A solução atende às necessidades de negócio definidas no desafio:

- **Cadastrar um veículo para venda** (marca, modelo, ano, cor, preço);
- **Editar os dados do veículo**;
- **Permitir a compra do veículo via internet** por pessoas cadastradas — o
  cadastro do comprador é feito anteriormente à compra;
- **Listar os veículos à venda**, ordenados por preço, do mais barato para o
  mais caro;
- **Listar os veículos vendidos**, com a mesma ordenação.

Um requisito central do desafio é que o **registro e a autorização de
compradores sejam totalmente apartados dos dados transacionais** de venda de
veículos. Por isso a solução é composta por **dois serviços independentes**:
um serviço de autenticação (baseado em **AWS Cognito**, onde vivem os dados de
clientes) e um serviço de vendas (com banco **PostgreSQL** próprio, onde vivem
veículos e compras).

O desafio também exige que toda mudança na solução (implantação ou alteração)
seja feita com **práticas de CI/CD e Pull Requests** — requisito atendido
pelos workflows de qualidade, infraestrutura e deploy descritos na seção
[Infraestrutura e Deploy](#infraestrutura-e-deploy).

## Arquitetura e Serviços

Este é um **monorepo**: os serviços e a infraestrutura vivem no mesmo
repositório por conveniência de versionamento e CI/CD, mas os **serviços são
completamente separados**. Cada um é autocontido — possui seu próprio código
(`src/`), testes, dependências (`pyproject.toml` + `uv.lock`), `Dockerfile`,
configuração de ambiente e documentação — e **não há nenhuma chamada em
runtime entre eles**. O único ponto de contato é indireto: o serviço de auth
emite tokens via Cognito e o serviço de vendas os valida localmente (JWKS),
sem falar com o serviço de auth.

Ambos os serviços seguem **Clean Architecture** (Ports & Adapters), em Python
com FastAPI e Pydantic.

| Serviço | Responsabilidade | Documentação |
|---------|------------------|--------------|
| **Auth** | Registro e login de compradores via AWS Cognito. Stateless — sem banco de dados próprio; os dados de clientes vivem apenas no Cognito, apartados do domínio transacional. | [services/auth/README.md](services/auth/README.md) |
| **Vendas** | Cadastro/edição de veículos, listagens ordenadas por preço e efetivação de compras, com PostgreSQL próprio. Autorização via validação local dos tokens do Cognito. | [services/vendas/README.md](services/vendas/README.md) |

Os READMEs de cada serviço detalham endpoints, arquitetura interna, variáveis
de ambiente, como rodar localmente e como testar — consulte-os diretamente;
este documento não repete esse conteúdo.

## Stack

- **Linguagem e dependências:** Python 3.13+, gerenciado exclusivamente com [uv](https://docs.astral.sh/uv/)
- **API:** FastAPI + Uvicorn, com Pydantic para entidades, schemas e validação
- **Banco de dados (vendas):** PostgreSQL 16, SQLAlchemy (async) + asyncpg, migrations com Alembic
- **Autenticação:** AWS Cognito (boto3 no auth; validação local de JWT via JWKS com PyJWT no vendas)
- **Logging:** loguru
- **Qualidade e testes:** pytest (+ pytest-asyncio, pytest-cov, testcontainers), ruff (lint/format), ty (type check), SonarCloud e pre-commit
- **Containers:** Docker (multistage build) e Docker Compose
- **Infraestrutura:** Terraform (state remoto no HCP Terraform) sobre AWS — VPC, EC2, RDS, Cognito, ECR, S3 e SSM; emulador floci para testes locais
- **CI/CD:** GitHub Actions (qualidade, infra e deploy)

## Infraestrutura e Deploy

Toda a infraestrutura é definida como código (**Terraform**) e operada por
três workflows de GitHub Actions: qualidade (lint, type check, testes e
SonarCloud em PRs), infra (provisionamento) e deploy (build das imagens e
implantação). Os guias abaixo cobrem cada ambiente:

### Deploy Oficial na AWS (produção)

Guia completo em **[infra/README.md](infra/README.md)** — pré-requisitos,
passo a passo de setup (SonarCloud, HCP Terraform, IAM, secrets do GitHub),
provisionamento dos recursos AWS (VPC, EC2, RDS, Cognito, ECR, SSM), operação
dos workflows de CI/CD e como destruir o ambiente.

### Deploy Local para Testes (desenvolvimento)

Guia em **[infra/local/README.md](infra/local/README.md)** — como testar o
mesmo stack Terraform de produção localmente contra o emulador **floci**
(compatível com LocalStack), sem gastar AWS real, incluindo os contornos
necessários do emulador e os modos de execução (host ou Docker Compose).

Para rodar apenas os serviços localmente (sem provisionar infraestrutura),
siga as instruções de execução local nos READMEs de cada serviço, listados na
seção [Arquitetura e Serviços](#arquitetura-e-serviços).

## Estrutura do Repositório

```
tech-challenge-3/
├── services/
│   ├── auth/        # serviço de autenticação (Cognito) — ver README próprio
│   └── vendas/      # serviço de veículos e compras (PostgreSQL) — ver README próprio
├── infra/
│   ├── stack/       # módulo Terraform compartilhado (VPC, EC2, RDS, Cognito, ECR, ...)
│   ├── main/        # root de produção (HCP Terraform) — ver infra/README.md
│   └── local/       # root de teste local (emulador floci) — ver infra/local/README.md
├── deploy/          # compose de produção + script executado na EC2 via SSM
└── .github/
    └── workflows/   # quality.yml, infra.yml, deploy.yml
```
