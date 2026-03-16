class ConsultaNaoEncontradaException(Exception):
    """Levantada quando nenhum resultado é encontrado para o identificador informado."""

    def __init__(self, termo: str, tipo: str) -> None:
        self.termo = termo
        self.tipo = tipo
        super().__init__(f"Nenhum resultado encontrado para {tipo}: {termo}")


class TimeoutConsultaException(Exception):
    """Levantada quando a consulta ultrapassa o tempo máximo configurado."""

    def __init__(self, identificador: str | None = None) -> None:
        msg = "Não foi possível retornar os dados no tempo de resposta solicitado"
        if identificador:
            msg = f"{msg} para o identificador informado"
        self.mensagem = msg
        super().__init__(msg)


class ErroNavegacaoException(Exception):
    """Levantada quando ocorre falha inesperada durante a navegação."""

    def __init__(self, detalhe: str) -> None:
        self.detalhe = detalhe
        super().__init__(f"Erro durante a navegação: {detalhe}")
