workspace "Tech Challenge 3 - Plataforma de Revenda de Veículos" "Modelo C4 (as-is) do monorepo: serviços de Auth e Vendas, banco de dados e integração com AWS Cognito." {

    model {
        comprador = person "Comprador" "Pessoa cadastrada que consulta veículos disponíveis e realiza compras pela internet." "Ator"
        administrador = person "Administrador" "Usuário do grupo 'admin' (Cognito) responsável por cadastrar e editar veículos para venda." "Ator"

        cognito = softwareSystem "AWS Cognito" "Provedor de identidade gerenciado (User Pool 'tc3-users'). Armazena os dados dos clientes, emite e assina os tokens JWT (access/refresh) e publica as chaves públicas via JWKS." "Sistema Externo"

        plataforma = softwareSystem "Plataforma de Revenda de Veículos" "Permite o cadastro, edição, listagem e venda de veículos automotores pela internet, com registro e autorização de compradores totalmente apartados dos dados transacionais." {

            authApi = container "Auth API" "Serviço de registro e login de compradores. Stateless e sem banco de dados próprio: os dados de clientes vivem apenas no Cognito. Endpoints: POST /v1/auth/register, POST /v1/auth/login, GET /health." "Python, FastAPI, uvicorn, boto3 (porta 8000)" "Aplicação Web"

            vendasApi = container "Vendas API" "Serviço transacional de veículos: cadastro/edição (admin), listagem paginada por preço e compra atômica. Valida os access tokens do Cognito localmente via JWKS, sem chamadas à Auth API em runtime. Endpoints: /v1/veiculos, /v1/compras, /health." "Python, FastAPI, uvicorn, SQLAlchemy async, PyJWT (porta 8001)" "Aplicação Web"

            vendasDb = container "Banco de Dados de Vendas" "Armazena as tabelas 'veiculos' e 'vendas'. PostgreSQL 16 em RDS (subnets privadas) em produção; container postgres:16-alpine no ambiente local. Migrações gerenciadas via Alembic." "PostgreSQL 16 (AWS RDS db.t3.micro)" "Banco de Dados"
        }

        # Atores -> Containers
        comprador -> authApi "Registra-se e autentica para obter o access token" "HTTPS/JSON"
        comprador -> vendasApi "Lista veículos disponíveis/vendidos e realiza compras" "HTTPS/JSON (Bearer JWT)"
        administrador -> authApi "Autentica para obter o access token" "HTTPS/JSON"
        administrador -> vendasApi "Cadastra e edita veículos para venda" "HTTPS/JSON (Bearer JWT com claim cognito:groups=admin)"

        # Containers -> Sistema externo
        authApi -> cognito "Registra usuários (SignUp, AdminConfirmSignUp) e autentica (InitiateAuth USER_PASSWORD_AUTH)" "boto3/HTTPS"
        vendasApi -> cognito "Obtém as chaves públicas (JWKS) para validar a assinatura RS256 dos tokens localmente" "HTTPS"

        # Container -> Banco de dados
        vendasApi -> vendasDb "Lê e escreve veículos e vendas" "SQLAlchemy async/asyncpg (TCP/5432)"
    }

    views {
        systemContext plataforma "ContextoDoSistema" "Visão de contexto: atores, a plataforma e o provedor de identidade externo (AWS Cognito)." {
            include *
            autoLayout lr
        }

        container plataforma "Containers" "Visão de containers: Auth API (stateless), Vendas API e seu banco PostgreSQL. Não há comunicação em runtime entre Auth e Vendas — a integração ocorre via tokens JWT emitidos pelo Cognito." {
            include *
            autoLayout lr
        }

        styles {
            element "Ator" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Sistema Externo" {
                background #999999
                color #ffffff
            }
            element "Aplicação Web" {
                shape roundedBox
                background #438dd5
                color #ffffff
            }
            element "Banco de Dados" {
                shape cylinder
                background #2a6a9e
                color #ffffff
            }
        }
    }
}
