"""Presenter de mascaramento de CPF (minimizacao de PII nas respostas)."""

_CPF_TAMANHO = 11


def mascarar_cpf(cpf: str) -> str:
    """Mascara um CPF para exibicao (`123.***.***-09`).

    Normaliza o CPF (remove formatacao) e mantem apenas os 3 primeiros digitos
    e os 2 verificadores; o CPF completo so aparece no endpoint administrativo
    (justificado pela documentacao da venda).

    Args:
        cpf: CPF normalizado (11 digitos) ou formatado (XXX.XXX.XXX-XX).

    Returns:
        CPF mascarado, ou o valor original se nao tiver 11 digitos
        (defensivo; nunca esperado para dados gravados por este servico).
    """
    # Normaliza: remove tudo que nao eh digito
    digitos = "".join(caractere for caractere in cpf if caractere.isdigit())
    if len(digitos) != _CPF_TAMANHO:
        return cpf
    return f"{digitos[:3]}.***.***-{digitos[9:]}"
