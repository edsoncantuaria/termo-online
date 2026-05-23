from nucleo.ranqueada import CalcularDelta, EloDePontos, MultiplicadorDelta


def test_vitoria_contra_mais_forte_da_mais_pontos():
    d = CalcularDelta(1000, 1200, True)
    assert 14 <= d <= 24


def test_derrota_perde_entre_7_e_14():
    d = CalcularDelta(1000, 1200, False)
    assert -14 <= d <= -7


def test_inicio_ganha_mais_e_perde_menos():
    assert CalcularDelta(100, 100, True) > CalcularDelta(2500, 2500, True)
    assert abs(CalcularDelta(100, 100, False)) < abs(CalcularDelta(2500, 2500, False))


def test_multiplicador_favorece_inicio():
    assert MultiplicadorDelta(50, True) > MultiplicadorDelta(3000, True)
    assert MultiplicadorDelta(50, False) < MultiplicadorDelta(3000, False)


def test_elo_papelao_inicio():
    assert EloDePontos(0) == "papelao"
    assert EloDePontos(200) == "papelao"


def test_pontos_iniciais_zero():
    from nucleo.ranqueada import PONTOS_INICIAIS

    assert PONTOS_INICIAIS == 0


def test_elo_estrela():
    assert EloDePontos(3300) == "estrela"
