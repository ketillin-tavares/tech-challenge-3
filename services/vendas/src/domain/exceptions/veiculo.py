"""Excecoes de dominio do contexto de Veiculo."""

from uuid import UUID

from src.domain.exceptions.base import DomainError


class VeiculoNaoEncontradoError(DomainError):
    """Veiculo inexistente para o identificador informado."""

    def __init__(self, veiculo_id: UUID) -> None:
        """Inicializa o erro com o identificador procurado.

        Args:
            veiculo_id: Identificador do veiculo nao encontrado.
        """
        self.veiculo_id = veiculo_id
        super().__init__(f"Veiculo {veiculo_id} nao encontrado.")


class VeiculoIndisponivelError(DomainError):
    """Tentativa de vender um veiculo que nao esta DISPONIVEL (ex.: ja vendido)."""

    def __init__(self, veiculo_id: UUID) -> None:
        """Inicializa o erro com o identificador do veiculo afetado.

        Args:
            veiculo_id: Identificador do veiculo que nao pode ser vendido.
        """
        self.veiculo_id = veiculo_id
        super().__init__(f"Veiculo {veiculo_id} nao esta disponivel para venda.")


class VeiculoVendidoNaoEditavelError(DomainError):
    """Tentativa de editar um veiculo que ja foi VENDIDO (estado terminal)."""

    def __init__(self, veiculo_id: UUID) -> None:
        """Inicializa o erro com o identificador do veiculo afetado.

        Args:
            veiculo_id: Identificador do veiculo que nao pode ser editado.
        """
        self.veiculo_id = veiculo_id
        super().__init__(f"Veiculo {veiculo_id} ja foi vendido e nao pode ser editado.")
