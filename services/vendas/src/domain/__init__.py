"""Camada Domain (Entities) do servico de vendas.

Unica camada sem dependencias externas (exceto `pydantic`, excecao aceita no
CLAUDE.md). Define as entidades (Veiculo, Venda), Value Objects (Preco, Ano,
StatusVeiculo, ClienteAutenticado), excecoes de dominio e os Ports de
persistencia (VeiculoRepository / VendaRepository / UnitOfWork).

O registro/login de clientes vive no servico de auth (apartado); aqui o
dominio referencia apenas o id opaco (`sub`) do cliente autenticado -- zero PII.
"""
