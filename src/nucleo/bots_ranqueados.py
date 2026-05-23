"""Bots ranqueados — populam fila, ranking e duelos 1v1 (sem conta real).

Medida temporária de lançamento: garante oponentes nos elos baixos quando não há
humano na fila, para o jogador ainda ganhar RP. Com a base crescendo, desative via
``TERM0_BOTS_RANQUEADOS=0`` (só PvP real).
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass

from .matchmaking_competitivo import JanelaRpBot
from .ranqueada import ELOS, EloDePontos, NomeEloExibicao

TOTAL_BOTS = 100

# RP máximo de bot: abaixo de Prata (sem bots em Prata, Ouro, Platina, Diamante, Estrela).
RP_MINIMO_PRATA = next(Min for Id, Min, _ in ELOS if Id == "prata")
RP_MAXIMO_BOTS = RP_MINIMO_PRATA - 1

# Só elos baixos — densidade maior em Papelão/Madeira (iniciantes ganham RP).
_QUANTIDADE_POR_ELO: tuple[tuple[str, int], ...] = (
    ("papelao", 34),
    ("madeira", 26),
    ("ferro", 20),
    ("bronze", 20),
)
assert sum(Q for _, Q in _QUANTIDADE_POR_ELO) == TOTAL_BOTS

ELOS_COM_BOTS = frozenset(Elo for Elo, _ in _QUANTIDADE_POR_ELO)

MINIMOS_BOTS_POR_ELO: dict[str, int] = {
    Elo: max(4, Qtd - 4) for Elo, Qtd in _QUANTIDADE_POR_ELO
}

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


def BotsRanqueadosAtivos() -> bool:
    """``TERM0_BOTS_RANQUEADOS=0`` desliga reserva e duelo contra bot (futuro)."""
    return os.environ.get("TERM0_BOTS_RANQUEADOS", "1").lower() not in (
        "0",
        "false",
        "no",
    )


def _FaixasPorElo() -> dict[str, tuple[int, int]]:
    return {Id: (Minimo, Maximo) for Id, Minimo, Maximo in ELOS}


def _PontosNaFaixaElo(Rng: random.Random, Minimo: int, Maximo: int, Indice: int, Total: int) -> int:
    """Distribui RP dentro da faixa; nos elos baixos inclui valores perto de 0 RP."""
    Largura = Maximo - Minimo
    if Largura <= 0:
        return Minimo
    if Minimo == 0 and Total >= 8:
        # Papelão (0 RP): faixas baixas para parear com iniciantes
        Faixas = (
            (0, min(80, Maximo)),
            (80, min(200, Maximo)),
            (200, Maximo),
        )
        Lo, Hi = Faixas[Indice % len(Faixas)]
        if Hi <= Lo:
            Hi = Lo + 1
        return Rng.randint(Lo, Hi)
    # Demais elos: leve viés para o terço inferior da faixa (mais acessível)
    T = (Indice + 0.3) / max(1, Total)
    T = min(1.0, T * T * 1.15)
    return Minimo + int(T * Largura)


def _GerarBots() -> list[BotRanqueado]:
    Rng = random.Random(42)
    Vistos: set[str] = set()
    Lista: list[BotRanqueado] = []
    Faixas = _FaixasPorElo()
    I = 0
    for EloId, Quantidade in _QUANTIDADE_POR_ELO:
        Minimo, Maximo = Faixas[EloId]
        Maximo = min(Maximo, RP_MAXIMO_BOTS)
        for J in range(Quantidade):
            while True:
                Nome = Rng.choice(_NOMES)
                Suf = Rng.choice(_SUFIXOS)
                Nick = (Nome + Suf).lower()[:20]
                if Nick not in Vistos and len(Nick) >= 3:
                    Vistos.add(Nick)
                    break
            Pontos = _PontosNaFaixaElo(Rng, Minimo, Maximo, J, Quantidade)
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


def ContarBotsPorElo() -> dict[str, int]:
    Contagem = {Id: 0 for Id, _, _ in ELOS}
    for B in BOTS:
        Contagem[EloDePontos(B.Pontos)] += 1
    return Contagem


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
    if not BotsRanqueadosAtivos():
        return None
    Livres = [
        B
        for B in BOTS
        if B.Id not in _BotsReservados
        and B.Id not in _BotsEmPartida
        and B.Pontos <= RP_MAXIMO_BOTS
        and EloDePontos(B.Pontos) in ELOS_COM_BOTS
    ]
    if not Livres:
        return None
    EloJogador = EloDePontos(PontosJogador)
    Proximos = sorted(
        Livres, key=lambda B: abs(B.Pontos - PontosJogador)
    )
    JanelaRp = JanelaRpBot(PontosJogador, SegundosEspera)
    Janela = [B for B in Proximos if abs(B.Pontos - PontosJogador) <= JanelaRp]
    MesmoElo = [B for B in (Janela or Proximos) if EloDePontos(B.Pontos) == EloJogador]
    Pool = (MesmoElo or Janela or Proximos)[:12]
    return random.choice(Pool)


def ListarBotsProximos(Pontos: int, Limite: int = 12) -> list[BotRanqueado]:
    if not BotsRanqueadosAtivos():
        return []
    Livres = [
        B
        for B in BOTS
        if B.Id not in _BotsReservados
        and B.Id not in _BotsEmPartida
        and B.Pontos <= RP_MAXIMO_BOTS
    ]
    EloJogador = EloDePontos(Pontos)
    Ordenados = sorted(Livres, key=lambda B: abs(B.Pontos - Pontos))
    MesmoElo = [B for B in Ordenados if EloDePontos(B.Pontos) == EloJogador]
    if MesmoElo:
        return MesmoElo[:Limite]
    return Ordenados[:Limite]


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
