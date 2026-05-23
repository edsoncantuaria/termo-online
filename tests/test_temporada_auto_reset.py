"""Reset automático de temporada ao mudar o mês."""

import pytest

from nucleo import persistencia
from nucleo.temporada_ranqueada import IdTemporadaAtual


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "temp.db")
    persistencia.InicializarBanco()
    return tmp_path


def test_garantir_temporada_reseta_contadores(banco):
    Id = persistencia.CriarConta("temp_user", "h", "s", EhVisitante=False)
    persistencia.AtualizarPontosRanqueada(Id, 50)
    persistencia.IncrementarVitoriaRanqueada(Id)
    C = persistencia.ObterContaPorId(Id)
    assert C["partidas_temporada"] == 1
    assert C["vitorias_temporada"] == 1

    persistencia.DefinirMetaSistema(
        "temporada_ranqueada_id", "1999-01"
    )
    persistencia.GarantirTemporadaRanqueadaAtual()

    C2 = persistencia.ObterContaPorId(Id)
    assert C2["partidas_temporada"] == 0
    assert C2["vitorias_temporada"] == 0
    assert C2["partidas_ranqueadas"] == 1
    assert persistencia.ObterMetaSistema("temporada_ranqueada_id") == IdTemporadaAtual()
