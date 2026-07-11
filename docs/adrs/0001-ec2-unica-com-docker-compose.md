# ADR 0001 — EC2 única com Docker Compose como plataforma de execução

## Status

Aceita

## Contexto

A plataforma precisa rodar dois serviços containerizados (Auth e Vendas) na
AWS, com deploy automatizado via CI/CD, para um projeto de fase de curso
(Pós-Tech SOAT — Fase 3). As restrições que pesaram na decisão:

- **Custo**: o ambiente fica de pé por semanas durante a fase, pago do próprio
  bolso. O orçamento-alvo é o mínimo que ainda demonstre uma arquitetura real
  (IaC, CI/CD, rede privada para o banco).
- **Carga**: tráfego de avaliação acadêmica — poucas requisições, um usuário
  por vez. Não há requisito de alta disponibilidade nem SLA.
- **Escopo da entrega**: o desafio exige funcionamento correto, deploy
  automatizado e mudanças via PR — não exige redundância nem escala.

As opções consideradas para orquestrar os containers:

1. **EC2 única + Docker Compose** (escolhida): uma t3.micro com EIP, imagens
   baixadas do ECR, stack definida em `deploy/docker-compose.prod.yml`,
   deploy disparado por SSM Run Command (sem SSH).
2. **ECS Fargate**: serviços gerenciados, sem instância para administrar.
   Porém o custo mínimo realista sobe: além das tasks (~US$ 9/mês cada uma em
   0.25 vCPU/0.5 GB), a exposição HTTP pede um ALB (~US$ 16+/mês), mais que
   dobrando a estimativa atual. Traria service discovery, deploy rolling e
   restart automático nativos.
3. **EKS**: só o control plane custa ~US$ 73/mês, mais nós ou Fargate
   profiles. A complexidade operacional (manifests, upgrades de cluster,
   add-ons) é desproporcional a dois serviços stateless de um projeto de
   curso.

## Decisão

Rodar os dois serviços em **uma única instância EC2 t3.micro com Docker
Compose**, com o banco em RDS separado (subnets privadas). A decisão é
**consciente e orientada a custo**: ~US$ 23/mês no total (EC2 + RDS + volumes;
ver estimativa em [infra/README.md](../../infra/README.md#custos-estimativa-mensal)),
contra alternativas gerenciadas que dobrariam ou triplicariam esse valor sem
benefício proporcional para a carga e o escopo desta fase.

O deploy permanece 100% automatizado e auditável: build no GitHub Actions,
push para o ECR com tags `latest` + SHA do commit, e execução na instância via
SSM Run Command. O ID da instância é resolvido em runtime via SSM Parameter
Store, então recriar a EC2 não quebra o pipeline.

## Consequências

### Negativas (aceitas)

- **Ponto único de falha**: se a instância cair, as duas APIs ficam fora do ar
  até a EC2 se recuperar (o dado persistente está no RDS, não na instância).
- **Sem redundância nem auto-scaling**: não há réplicas, health-check com
  substituição automática, nem absorção de picos de tráfego.
- **Rollback manual**: não há estratégia nativa de rollback; reverter é
  re-executar o workflow de deploy apontando para o SHA anterior (as imagens
  ficam retidas no ECR por tag de commit).
- **Downtime breve a cada deploy**: o `docker compose up -d` recria os
  containers na própria instância, sem rolling update.

### Positivas

- **Custo mínimo e previsível** (~US$ 23/mês), compatível com um ambiente
  pago do próprio bolso durante a fase.
- **Simplicidade operacional**: uma instância, um compose file versionado no
  repo, logs acessíveis por Session Manager — sem camadas de orquestração
  para depurar.
- **Nada disso compromete a arquitetura da aplicação**: os serviços são
  stateless (estado no RDS e no Cognito) e as imagens são as mesmas que
  rodariam em ECS/EKS. Migrar depois é trocar a camada de execução, não os
  serviços.

## Quando revisitar

Migrar para ECS Fargate (a alternativa natural, antes de considerar EKS) se o
projeto sair do contexto acadêmico e passar a exigir: disponibilidade real
(usuários externos), deploys sem downtime, ou escala horizontal. O gatilho de
custo também vale na direção oposta: se o orçamento deixar de ser restrição, o
ALB + Fargate elimina as consequências negativas listadas acima.
