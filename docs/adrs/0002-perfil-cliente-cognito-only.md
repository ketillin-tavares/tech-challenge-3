# ADR 0002 — Perfil do cliente (nome e CPF) exclusivamente no Cognito

## Status

Aceita

## Contexto

O enunciado do challenge exige modelagem de cliente suficiente para documentar
uma venda — no mínimo **nome e CPF** do comprador — e a resposta à pergunta
"quem comprou este veículo?". Até então o cadastro capturava apenas email e
senha, e a `Venda` guarda somente o `sub` opaco do JWT (decisão mantida: o
serviço de vendas **não** armazena PII).

Duas abordagens foram consideradas para o perfil:

1. **Cognito-only** (escolhida): atributo padrão `name` + custom attribute
   `custom:cpf`, gravados atomicamente no `SignUp`. Leitura via `GetUser`
   (com o access token do próprio cliente) e `ListUsers` com filtro por `sub`
   (endpoint administrativo).
2. **Perfil persistido no serviço de auth** (Postgres próprio): permitiria
   `UNIQUE(cpf)` real e consultas locais, mas exigiria banco no auth,
   dual-write Cognito+DB com compensação (`AdminDeleteUser` + IAM), roles
   PostgreSQL dedicadas e tratamento de usuários órfãos — maquinário
   desproporcional ao escopo do challenge.

## Decisão

**O perfil do cliente vive exclusivamente no Cognito.** O serviço de auth
segue stateless (sem banco, sem migrations, sem dual-write):

- `POST /v1/auth/register` exige `{email, senha, nome, cpf}`; o VO `Cpf`
  valida dígitos verificadores e **normaliza para dígitos-apenas** antes de
  qualquer persistência (formato canônico único).
- `GET /v1/clientes/me` usa `GetUser` autorizado pelo **próprio access token**
  (menor privilégio: nenhuma credencial IAM no read-path próprio).
- `GET /v1/clientes/{sub}` (admin) usa `ListUsers` com `Filter: sub = "..."`
  — o atributo `sub` é filtrável por contrato documentado da AWS; a igualdade
  `username == sub` **não** é garantida e por isso `AdminGetUser` não é usado.
- `custom:cpf` é `mutable = false`: gravável apenas no `SignUp`, inalterável
  depois (fecha auto-adulteração via `UpdateUserAttributes`).

### Política de PII (CPF)

- CPF **nunca** em logs nem em mensagens de exceção (mensagens fixas; a causa
  original fica só no traceback interno).
- Respostas: CPF **mascarado** (`123.***.***-09`) no eco do register e no
  `/me`; completo apenas no endpoint administrativo (documentação da venda).
- O conflito de cadastro responde `409 DADOS_JA_CADASTRADOS` genérico, com
  **rate limiting por IP** (slowapi) nos endpoints públicos.

## Consequências

### Limitações aceitas

- **Unicidade de CPF não é garantida**: custom attributes não são filtráveis
  em `ListUsers`, então não há como impedir dois emails com o mesmo CPF.
  Implicação concreta: cadastros duplicados/CPF de terceiro não são detectados.
  Aceitável no volume do challenge; mitigação futura: auditoria offline via
  export do pool.
- **Read-path de perfil depende do Cognito em runtime** (`GetUser`/`ListUsers`
  têm quota e latência; sem cache). Protegido por rate limit próprio
  (`RATELIMIT_CLIENTES`).
- **Oráculo residual de email no register**: 409 num signup público revela que
  o email existe (inerente a signup sem confirmação por email). Como só o
  conflito de email gera 409 hoje, o rótulo genérico é future-proofing; a
  mitigação real é o rate limit + log de conflitos repetidos (IP, sem PII).
- **CPF imutável**: correção de CPF digitado errado exige recadastro, e
  recadastro exige **deleção manual prévia do usuário por um humano**
  (console/CLI) — a role da aplicação intencionalmente não tem
  `AdminDeleteUser`.
- **Usuários legados** (criados antes desta decisão) retornam `nome`/`cpf`
  nulos no perfil (200, não 404 — o usuário existe e autentica). Estratégia:
  recriar os usuários seed do challenge.
- **Rate limit é por processo** (slowapi em memória). Premissa operacional:
  **1 worker uvicorn por serviço**; com N workers/réplicas os limites se
  diluem N× (gatilho para storage compartilhado, ex.: Redis).

### Regras operacionais

- **Todo usuário cliente nasce pelo `/v1/auth/register`**; criação manual no
  console fica restrita a administradores (que não compram) — senão a
  população sem CPF volta a crescer silenciosamente.
- **Runbook — conta presa em UNCONFIRMED** (falha entre `SignUp` e
  `AdminConfirmSignUp`: o email fica tomado, não loga e não re-registra):
  confirmar manualmente (`aws cognito-idp admin-confirm-sign-up`) ou deletar o
  usuário (`admin-delete-user`) via console/CLI com credencial humana, e
  orientar novo registro.
- **Terraform — nunca editar o bloco `schema` do `custom:cpf`**: adicionar
  custom attribute é aditivo (update in-place), mas alterar/remover força
  **replace do User Pool** (perde todos os usuários). Todo `terraform plan`
  que mostre `must be replaced` no pool deve ser abortado.

## Quando revisitar

Reintroduzir persistência própria de perfil (opção 2) se surgir necessidade
real de **unicidade de CPF** (requisito fiscal/antifraude), de consultas em
massa (relatórios com join por CPF) ou de documento fiscal imutável — neste
último caso, como snapshot dos dados do comprador gravado na **efetivação** da
venda, complementando (não substituindo) o Cognito.
