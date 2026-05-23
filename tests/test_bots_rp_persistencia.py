"""RP dos bots persiste no SQLite entre reinícios lógicos."""

import importlib

import pytest

from nucleo import persistencia


@pytest.fixture()
def banco_isolado(tmp_path, monkeypatch):
    monkeypatch.setenv("TERM0_DATA", str(tmp_path))
    import nucleo.bots_ranqueados as br

    br._EstadoBotsCarregado = False
    br._PontosVivos.clear()
    br._PartidasBots.clear()
    br._VitoriasBots.clear()
    persistencia.InicializarBanco()
    br.InicializarEstadoBotsRanqueados()
    yield br
    br._EstadoBotsCarregado = False


def test_bot_rp_sobrevive_reinicio_modulo(banco_isolado):
    br = banco_isolado
    Bot = br.BOTS[0]
    Antes = br.PontosBotAtual(Bot.Id)
    br.AplicarResultadoDueloBot(f"bot-{Bot.Id}", Antes, True)
    Depois = br.PontosBotAtual(Bot.Id)
    assert Depois > Antes

    br._EstadoBotsCarregado = False
    br._PontosVivos.clear()
    br._PartidasBots.clear()
    br._VitoriasBots.clear()
    br.InicializarEstadoBotsRanqueados()
    assert br.PontosBotAtual(Bot.Id) == Depois
    assert br.EstatisticasBot(Bot.Id)[0] >= 1
