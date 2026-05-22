"""Bots ranqueados — populam fila, ranking e duelos 1v1 (sem conta real)."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .ranqueada import EloDePontos, NomeEloExibicao

TOTAL_BOTS = 100
from .matchmaking_competitivo import JanelaRpBot

_NOMES = (
    "Ana",
    "Bruno",
    "Carla",
    "Diego",
    "Elena",
    "Felipe",
    "Gabi",
    "Hugo",
    "Iris",
    "João",
    "Kira",
    "Leo",
    "Maya",
    "Nina",
    "Otávio",
    "Paula",
    "Rafa",
    "Sofia",
    "Thiago",
    "Ursula",
    "Vitor",
    "Wesley",
    "Yara",
    "Zeca",
    "Alice",
    "Beto",
    "Cadu",
    "Duda",
    "Edu",
    "Fabi",
    "Guto",
    "Helo",
    "Igor",
    "Jade",
    "Kiko",
    "Lia",
    "Milo",
    "Neco",
    "Oli",
    "Pietro",
    "Quim",
    "Rita",
    "Samu",
    "Tina",
    "Ugo",
    "Vivi",
    "Xande",
    "Yuri",
    "Zara",
)

_SUFIXOS = (
    "",
    "BR",
    "Pro",
    "X",
    "99",
    "777",
    "Oficial",
    "PT",
    "Game",
    "Word",
    "Termo",
    "Rank",
    "Elite",
    "Ninja",
    "Fox",
    "Wolf",
    "Star",
    "Ace",
    "Neo",
    "Max",
)


@dataclass(frozen=True)
class BotRanqueado:
    Id: str
    Nick: str
    Pontos: int


def _GerarBots() -> list[BotRanqueado]:
    Rng = random.Random(42)
    Vistos: set[str] = set()
    Lista: list[BotRanqueado] = []
    I = 0
    while len(Lista) < TOTAL_BOTS:
        Nome = Rng.choice(_NOMES)
        Suf = Rng.choice(_SUFIXOS)
        Nick = (Nome + Suf).lower()[:20]
        if Nick in Vistos or len(Nick) < 3:
            continue
        Vistos.add(Nick)
        # RP variado (0–~2700), mais jogadores no meio/baixo
        Pontos = int(Rng.betavariate(2.2, 4.5) * 2700)
        Lista.append(
            BotRanqueado(
                Id=f"bot_{I:03d}",
                Nick=Nick,
                Pontos=Pontos,
            )
        )
        I += 1
    return Lista


BOTS: list[BotRanqueado] = _GerarBots()
_BOTS_POR_ID: dict[str, BotRanqueado] = {B.Id: B for B in BOTS}
_BotsReservados: set[str] = set()
_BotsEmPartida: set[str] = set()


def ObterBot(Id: str) -> BotRanqueado | None:
    return _BOTS_POR_ID.get(Id)


def ContarBotsDisponiveis() -> int:
    return sum(
        1
        for B in BOTS
        if B.Id not in _BotsReservados and B.Id not in _BotsEmPartida
    )


def ReservarBot(Id: str) -> None:
    _BotsReservados.add(Id)


def LiberarReservaBot(Id: str | None) -> None:
    if Id:
        _BotsReservados.discard(Id)


def MarcarBotEmPartida(Id: str) -> None:
    _BotsReservados.discard(Id)
    _BotsEmPartida.add(Id)


def LiberarBotPartida(Id: str | None) -> None:
    if Id:
        _BotsEmPartida.discard(Id)
        _BotsReservados.discard(Id)


def LiberarBotsDaSala(Sala) -> None:
    for J in Sala.Jogadores.values():
        if not getattr(J, "EhBot", False):
            continue
        IdBot = J.IdJogador
        if IdBot.startswith("bot-"):
            LiberarBotPartida(IdBot[4:])


def EscolherBotParaPontos(
    PontosJogador: int, SegundosEspera: float = 0.0
) -> BotRanqueado | None:
    Livres = [
        B
        for B in BOTS
        if B.Id not in _BotsReservados and B.Id not in _BotsEmPartida
    ]
    if not Livres:
        return None
    Proximos = sorted(
        Livres, key=lambda B: abs(B.Pontos - PontosJogador)
    )
    JanelaRp = JanelaRpBot(PontosJogador, SegundosEspera)
    Janela = [B for B in Proximos if abs(B.Pontos - PontosJogador) <= JanelaRp]
    Pool = Janela[:12] if Janela else Proximos[:8]
    return random.choice(Pool)


def ListarBotsProximos(Pontos: int, Limite: int = 12) -> list[BotRanqueado]:
    Livres = [
        B
        for B in BOTS
        if B.Id not in _BotsReservados and B.Id not in _BotsEmPartida
    ]
    return sorted(Livres, key=lambda B: abs(B.Pontos - Pontos))[:Limite]


def BotParaRanking(B: BotRanqueado, Posicao: int) -> dict:
    Elo = EloDePontos(B.Pontos)
    return {
        "posicao": Posicao,
        "nick": B.Nick,
        "pontos": B.Pontos,
        "elo": Elo,
        "eloNome": NomeEloExibicao(Elo),
        "partidas": 0,
        "vitorias": 0,
        "ehBot": True,
        "souEu": False,
    }


def PontosBotPorIdJogador(IdJogador: str) -> int:
    if not IdJogador.startswith("bot-"):
        return 1000
    Bot = ObterBot(IdJogador[4:])
    return Bot.Pontos if Bot else 1000
