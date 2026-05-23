from nucleo.ranqueada import CalcularDelta, EloDePontos


def test_vitoria_contra_mais_forte_da_mais_pontos():
    d = CalcularDelta(1000, 1200, True)
    assert 16 <= d <= 20


def test_derrota_perde_entre_8_e_12():
    d = CalcularDelta(1000, 1200, False)
    assert -12 <= d <= -8


def test_elo_papelao_inicio():
    assert EloDePontos(0) == "papelao"
    assert EloDePontos(200) == "papelao"


def test_pontos_iniciais_zero():
    from nucleo.ranqueada import PONTOS_INICIAIS

    assert PONTOS_INICIAIS == 0


def test_elo_estrela():
    assert EloDePontos(3300) == "estrela"
