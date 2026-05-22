"""Regras de janela RP e pareamento ranqueado (competitivo, expansível no tempo)."""

from __future__ import annotations

import time

from .ranqueada import EloDePontos, ELOS

# Tempos da fila (segundos)
BUSCA_REAL_SEG = 4
ESPERA_BOT_SEG = 10

# Janela ±RP entre oponentes
JANELA_RP_INICIAL = 75
"""No começo da fila: duelos bem pareados (±75 RP)."""

JANELA_RP_CRESCIMENTO_POR_SEG = 12
"""A cada segundo esperando, a busca amplia +12 RP (máx. dos dois na fila)."""

JANELA_RP_MAXIMA = 320
"""Teto para PvP real — acima disso só entra oponente reservado/bot."""

JANELA_RP_MESMO_ELO_EXTRA = 45
"""Mesma faixa de elo: tolera um pouco mais de diferença de RP."""

JANELA_RP_BOT_BASE = 90
"""Bots: oponente com RP próximo ao seu (cresce com a espera)."""


def LarguraFaixaElo(Pontos: int) -> int:
    Elo = EloDePontos(Pontos)
    for Id, Minimo, Maximo in ELOS:
        if Id == Elo:
            return Maximo - Minimo + 1
    return 400


def SegundosNaFila(EntrouEm: float, Agora: float | None = None) -> float:
    return max(0.0, (Agora or time.time()) - EntrouEm)


def JanelaRpPermitida(Pontos: int, SegundosEspera: float) -> int:
    """
    Janela ±RP permitida para um jogador conforme tempo na fila.
    Ex.: 0s → 75 · 4s → ~123 · 10s → ~195 · 14s+ → até 320 (+ bônus de faixa).
    """
    Crescimento = int(SegundosEspera * JANELA_RP_CRESCIMENTO_POR_SEG)
    AjusteFaixa = min(50, LarguraFaixaElo(Pontos) // 8)
    return min(JANELA_RP_MAXIMA, JANELA_RP_INICIAL + Crescimento + AjusteFaixa)


def JanelaRpEntreJogadores(
    PontosA: int,
    SegundosA: float,
    PontosB: int,
    SegundosB: float,
) -> int:
    """Janela efetiva do duelo = o que cada um já 'liberou' pelo tempo na fila."""
    return max(
        JanelaRpPermitida(PontosA, SegundosA),
        JanelaRpPermitida(PontosB, SegundosB),
    )


def PodeParearRp(
    PontosA: int,
    SegundosA: float,
    PontosB: int,
    SegundosB: float,
) -> bool:
    Diff = abs(int(PontosA) - int(PontosB))
    Janela = JanelaRpEntreJogadores(PontosA, SegundosA, PontosB, SegundosB)
    if EloDePontos(PontosA) == EloDePontos(PontosB):
        Janela += JANELA_RP_MESMO_ELO_EXTRA
    return Diff <= Janela


def JanelaRpBot(PontosJogador: int, SegundosEspera: float) -> int:
    return min(
        JANELA_RP_MAXIMA,
        JANELA_RP_BOT_BASE + int(SegundosEspera * JANELA_RP_CRESCIMENTO_POR_SEG),
    )


def ScoreQualidadePar(
    PontosA: int,
    SegundosA: float,
    PontosB: int,
    SegundosB: float,
) -> int:
    """Menor = melhor partida (RP perto, mesma faixa, quem espera há mais tempo)."""
    Diff = abs(int(PontosA) - int(PontosB))
    Espera = max(SegundosA, SegundosB)
    Score = Diff * 1000 - int(Espera * 20)
    if EloDePontos(PontosA) == EloDePontos(PontosB):
        Score -= 12_000
    if Diff <= JANELA_RP_INICIAL:
        Score -= 3000
    return Score


def FaixaRpBusca(Pontos: int, SegundosEspera: float) -> tuple[int, int]:
    J = JanelaRpPermitida(Pontos, SegundosEspera)
    P = max(0, int(Pontos))
    return max(0, P - J), P + J


def ResumoJanelaCliente(Pontos: int, SegundosEspera: float) -> dict:
    J = JanelaRpPermitida(Pontos, SegundosEspera)
    MinRp, MaxRp = FaixaRpBusca(Pontos, SegundosEspera)
    return {
        "janelaRp": J,
        "rpMinimo": MinRp,
        "rpMaximo": MaxRp,
        "elo": EloDePontos(Pontos),
        "segundosBusca": int(SegundosEspera),
    }
