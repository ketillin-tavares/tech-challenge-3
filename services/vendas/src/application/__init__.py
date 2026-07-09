"""Camada Application (Use Cases) - regras de negocio da aplicacao.

Orquestra entidades e Ports para realizar casos de uso. Depende APENAS da
camada Domain (entidades e ports abstratos), nunca de implementacoes concretas.
Transacoes sao coordenadas via o port UnitOfWork.

Casos de uso (mesma Clean Architecture, sem modulo separado por contexto):
  - Transacional: CadastrarVeiculo, EditarVeiculo, ListarDisponiveis,
    ListarVendidos, ComprarVeiculo.
  - Identidade/Auth: RegistrarCliente, AutenticarCliente.

Preenchida nas tarefas T3 / T4b.
"""
