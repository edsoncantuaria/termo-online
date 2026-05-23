import pytest

from nucleo import controle_carga as cc


@pytest.fixture(autouse=True)
def resetar_contadores():
    with cc._Bloqueio:
        cc._ConexoesWsSala = 0
        cc._ConexoesWsLobby = 0
        cc._FilaEsperaServidor.clear()
    yield
    with cc._Bloqueio:
        cc._ConexoesWsSala = 0
        cc._ConexoesWsLobby = 0
        cc._FilaEsperaServidor.clear()


def test_ws_sala_aceita_ate_limite(monkeypatch):
    monkeypatch.setattr(cc, "MAX_CONEXOES_WS_SALA", 2)
    assert cc.PodeAceitarWsSala().Permitido
    cc.RegistrarConexaoWsSala()
    assert cc.PodeAceitarWsSala().Permitido
    cc.RegistrarConexaoWsSala()
    R = cc.PodeAceitarWsSala()
    assert not R.Permitido
    assert R.PosicaoFila == 1
    cc.LiberarConexaoWsSala()
    assert cc.PodeAceitarWsSala().Permitido


def test_fila_ranqueada_cheia(monkeypatch):
    monkeypatch.setattr(cc, "MAX_FILA_RANQUEADA", 1)
    assert cc.PodeEntrarFilaRanqueada(0, False).Permitido
    assert not cc.PodeEntrarFilaRanqueada(1, False).Permitido
    assert cc.PodeEntrarFilaRanqueada(1, True).Permitido


def test_criar_sala_limite(monkeypatch):
    monkeypatch.setattr(cc, "MAX_SALAS_ATIVAS", 3)
    assert cc.PodeCriarSala(2).Permitido
    assert not cc.PodeCriarSala(3).Permitido
