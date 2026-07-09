"""Casos de uso (Application) do BC Transacional de Veiculos e Vendas.

Cada use case recebe seus ports por injecao no construtor e expoe um unico
metodo assincrono `executar`. Dependem apenas de abstracoes (ports) e do
dominio, nunca de implementacoes concretas (DIP).
"""
