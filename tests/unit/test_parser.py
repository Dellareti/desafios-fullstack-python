from app.bot.parser import (
    limpar_texto,
    parse_competencia,
    parse_data_br_para_iso,
    parse_valor_monetario,
)


class TestLimparTexto:
    def test_remove_espacos_extras(self) -> None:
        assert limpar_texto("  João   da  Silva  ") == "João da Silva"

    def test_string_vazia(self) -> None:
        assert limpar_texto("") == ""

    def test_none(self) -> None:
        assert limpar_texto(None) == ""  # type: ignore[arg-type]


class TestParseValorMonetario:
    def test_valor_simples(self) -> None:
        assert parse_valor_monetario("R$ 600,00") == 600.0

    def test_valor_com_milhar(self) -> None:
        assert parse_valor_monetario("R$ 1.234,56") == 1234.56

    def test_valor_grande(self) -> None:
        assert parse_valor_monetario("R$ 10.000,00") == 10000.0

    def test_sem_valor(self) -> None:
        assert parse_valor_monetario("sem valor") == 0.0


class TestParseDataBrParaIso:
    def test_data_valida(self) -> None:
        assert parse_data_br_para_iso("15/03/1990") == "1990-03-15"

    def test_data_em_texto(self) -> None:
        assert parse_data_br_para_iso("Nascimento: 01/01/2000") == "2000-01-01"

    def test_sem_data(self) -> None:
        assert parse_data_br_para_iso("sem data aqui") is None

    def test_data_invalida(self) -> None:
        assert parse_data_br_para_iso("99/99/9999") is None


class TestParseCompetencia:
    def test_formato_mes_ano(self) -> None:
        resultado = parse_competencia("jan/2024")
        assert resultado == "01/2024"

    def test_formato_maiusculo(self) -> None:
        resultado = parse_competencia("DEZ/2023")
        assert resultado == "12/2023"

    def test_formato_ja_numerico(self) -> None:
        resultado = parse_competencia("03/2024")
        assert resultado == "03/2024"
