from nucleo.matchmaking_competitivo import (
    BUSCA_REAL_SEG,
    ESPERA_BOT_SEG,
    JANELA_RP_INICIAL,
    JANELA_RP_MAXIMA,
    PodeParearRp,
    JanelaRpPermitida,
    ScoreQualidadePar,
)


def test_janela_inicial_apertada():
    assert JanelaRpPermitida(1000, 0) == JANELA_RP_INICIAL + min(50, 400 // 8)


def test_janela_cresce_com_tempo():
    J0 = JanelaRpPermitida(1000, 0)
    J4 = JanelaRpPermitida(1000, 4)
    J14 = JanelaRpPermitida(1000, 14)
    assert J4 > J0
    assert J14 > J4
    assert J14 <= JANELA_RP_MAXIMA + 50


def test_nao_pareia_muito_distante_no_inicio():
    assert not PodeParearRp(500, 0, 900, 0)


def test_pareia_proximo_no_inicio():
    assert PodeParearRp(1000, 0, 1050, 0)


def test_espera_longa_amplia_pareamento():
    assert PodeParearRp(500, 14, 780, 14)


def test_mesmo_elo_facilita_par():
    assert PodeParearRp(100, 0, 200, 0)


def test_melhor_par_menor_score():
    S_proximo = ScoreQualidadePar(1000, 5, 1020, 5)
    S_longe = ScoreQualidadePar(1000, 5, 1200, 5)
    assert S_proximo < S_longe


def test_busca_real_antes_do_bot():
    assert BUSCA_REAL_SEG == 2
    assert ESPERA_BOT_SEG == 5
