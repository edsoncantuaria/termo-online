"""Bots acumulam RP após duelos (comportamento humano)."""

from nucleo.bots_ranqueados import (
    AplicarResultadoDueloBot,
    BOTS,
    PontosBotAtual,
    _PontosVivos,
)


def test_bot_ganha_rp_apos_vitoria():
    Bot = BOTS[0]
    _PontosVivos.pop(Bot.Id, None)
    Antes = PontosBotAtual(Bot.Id)
    AplicarResultadoDueloBot(f"bot-{Bot.Id}", Antes, True)
    assert PontosBotAtual(Bot.Id) > Antes


def test_bot_perde_rp_apos_derrota():
    Bot = BOTS[1]
    _PontosVivos.pop(Bot.Id, None)
    Antes = PontosBotAtual(Bot.Id)
    AplicarResultadoDueloBot(f"bot-{Bot.Id}", Antes + 200, False)
    assert PontosBotAtual(Bot.Id) < Antes
