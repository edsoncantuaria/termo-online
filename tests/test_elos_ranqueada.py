import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.ranqueada import (
    EloDePontos,
    ELOS,
    ListarElosApi,
    MontarCamposRankExibicao,
    NomeEloExibicao,
    RotuloRankConta,
)
from nucleo import persistencia


def test_faixas_elo_com_prata_entre_bronze_e_ouro():
    Ids = [E[0] for E in ELOS]
    assert Ids.index("bronze") < Ids.index("prata") < Ids.index("ouro")
    assert EloDePontos(0) == "papelao"
    assert EloDePontos(500) == "madeira"
    assert EloDePontos(1700) == "prata"
    assert EloDePontos(2100) == "ouro"
    assert EloDePontos(3300) == "estrela"


def test_sem_rank_ate_primeira_partida():
    assert RotuloRankConta(0, 0) == "Sem Rank"
    Campos = MontarCamposRankExibicao(0, 500)
    assert Campos["semRank"] is True
    assert Campos["rotuloRank"] == "Sem Rank"
    assert Campos["elo"] is None

    Campos2 = MontarCamposRankExibicao(1, 50)
    assert Campos2["semRank"] is False
    assert Campos2["rotuloRank"] == "Papelão"


def test_listar_elos_api_tem_cores():
    Elos = ListarElosApi()
    assert any(E["id"] == "prata" for E in Elos)
    Prata = next(E for E in Elos if E["id"] == "prata")
    assert Prata["nome"] == "Prata"
    assert "fundo" in Prata and "classeCss" in Prata


def test_partidas_temporada_e_total_incrementam(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "temp.db")
    persistencia.InicializarBanco()
    Id = persistencia.CriarConta("teste_elo", "h", "s", EhVisitante=False)
    persistencia.AtualizarPontosRanqueada(Id, 20)
    C = persistencia.ObterContaPorId(Id)
    assert C["partidas_ranqueadas"] == 1
    assert C["partidas_temporada"] == 1
    persistencia.IncrementarVitoriaRanqueada(Id)
    C2 = persistencia.ObterContaPorId(Id)
    assert C2["vitorias_ranqueadas"] == 1
    assert C2["vitorias_temporada"] == 1
    N = persistencia.ResetarEstatisticasTemporadaRanqueada()
    assert N >= 1
    C3 = persistencia.ObterContaPorId(Id)
    assert C3["partidas_temporada"] == 0
    assert C3["partidas_ranqueadas"] == 1
