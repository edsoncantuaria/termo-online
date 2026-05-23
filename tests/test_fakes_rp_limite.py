"""RP máximo de contas fake (bots + população passiva): abaixo de Prata."""

from nucleo.bots_ranqueados import BOTS, RP_MAXIMO_BOTS
from nucleo.ranqueada import EloDePontos
from nucleo.ranking_ranqueado import _POPULACAO_PASSIVA

_ELOS_ALTO = frozenset({"prata", "ouro", "platina", "diamante", "estrela"})


def test_populacao_passiva_abaixo_de_prata():
    assert len(_POPULACAO_PASSIVA) >= 2000
    for E in _POPULACAO_PASSIVA:
        assert E["pontos"] <= RP_MAXIMO_BOTS
        assert EloDePontos(E["pontos"]) not in _ELOS_ALTO


def test_reset_bots_limpa_banco(tmp_path, monkeypatch):
    from nucleo import persistencia
    from nucleo.bots_ranqueados import PontosBotAtual, ResetarBotsRanqueadosParaPadrao

    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "reset.db")
    persistencia.InicializarBanco()
    B = BOTS[0]
    persistencia.SalvarEstadoBotRanqueado(B.Id, 9999, 50, 30)

    import nucleo.bots_ranqueados as br

    br._EstadoBotsCarregado = False
    br.InicializarEstadoBotsRanqueados()
    assert PontosBotAtual(B.Id) == RP_MAXIMO_BOTS  # clamp ao carregar

    br._EstadoBotsCarregado = False
    N = ResetarBotsRanqueadosParaPadrao()
    assert N >= 1
    assert PontosBotAtual(B.Id) == B.Pontos
    assert persistencia.ListarEstadoBotsRanqueados() == {}
