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
_PontosVivos: dict[str, int] = {B.Id: B.Pontos for B in BOTS}
_PartidasBots: dict[str, int] = {}
_VitoriasBots: dict[str, int] = {}
_EstadoBotsCarregado = False


def ResetarBotsRanqueadosParaPadrao() -> int:
    """Zera evolução dos bots no banco e na memória (valores iniciais de lançamento)."""
    global _EstadoBotsCarregado, _PontosVivos, _PartidasBots, _VitoriasBots

    from . import persistencia

    Removidos = persistencia.LimparEstadoBotsRanqueados()
    _PontosVivos = {B.Id: B.Pontos for B in BOTS}
    _PartidasBots.clear()
    _VitoriasBots.clear()
    _BotsReservados.clear()
    _BotsEmPartida.clear()
    _EstadoBotsCarregado = True
    return Removidos


def InicializarEstadoBotsRanqueados() -> None:
    """Carrega RP dos bots do SQLite (chamar após ``InicializarBanco``)."""
    global _EstadoBotsCarregado
    if _EstadoBotsCarregado:
        return
    from . import persistencia

    Salvo = persistencia.ListarEstadoBotsRanqueados()
    for B in BOTS:
        Row = Salvo.get(B.Id)
        if Row:
            _PontosVivos[B.Id] = max(0, min(RP_MAXIMO_BOTS, int(Row["pontos"])))
            _PartidasBots[B.Id] = max(0, int(Row["partidas"]))
            _VitoriasBots[B.Id] = max(0, int(Row["vitorias"]))
        else:
            _PontosVivos.setdefault(B.Id, B.Pontos)
    _EstadoBotsCarregado = True


def _PersistirBot(IdBot: str) -> None:
    if IdBot not in _BOTS_POR_ID:
        return
    from . import persistencia

    persistencia.SalvarEstadoBotRanqueado(
        IdBot,
        PontosBotAtual(IdBot),
        _PartidasBots.get(IdBot, 0),
        _VitoriasBots.get(IdBot, 0),
    )


def _IdBotInterno(IdJogador: str) -> str | None:
    if IdJogador.startswith("bot-"):
        return IdJogador[4:]
    if IdJogador.startswith("bot_"):
        return IdJogador
    return None


def PontosBotAtual(IdBot: str) -> int:
    if not _EstadoBotsCarregado:
        InicializarEstadoBotsRanqueados()
    return _PontosVivos.get(IdBot, _BOTS_POR_ID[IdBot].Pontos if IdBot in _BOTS_POR_ID else 0)


def EstatisticasBot(IdBot: str) -> tuple[int, int]:
    return _PartidasBots.get(IdBot, 0), _VitoriasBots.get(IdBot, 0)


def AplicarResultadoDueloBot(IdJogador: str, PontosHumano: int, VenceuBot: bool) -> None:
    """Atualiza RP do bot após duelo (evolui como jogador real)."""
    IdBot = _IdBotInterno(IdJogador)
    if not IdBot or IdBot not in _BOTS_POR_ID:
        return
    from .ranqueada import CalcularDelta

    PontosBot = PontosBotAtual(IdBot)
    Delta = CalcularDelta(PontosBot, int(PontosHumano), VenceuBot)
    _PontosVivos[IdBot] = max(0, min(RP_MAXIMO_BOTS, PontosBot + Delta))
    _PartidasBots[IdBot] = _PartidasBots.get(IdBot, 0) + 1
    if VenceuBot:
        _VitoriasBots[IdBot] = _VitoriasBots.get(IdBot, 0) + 1
    _PersistirBot(IdBot)


def ContarBotsPorElo() -> dict[str, int]:
    Contagem = {Id: 0 for Id, _, _ in ELOS}
    for B in BOTS:
        Contagem[EloDePontos(PontosBotAtual(B.Id))] += 1
    return Contagem


def ObterBot(Id: str) -> BotRanqueado | None:
    return _BOTS_POR_ID.get(Id)


def ObterBotPorNick(Nick: str) -> BotRanqueado | None:
    """Busca bot pelo nick exibido (mesmo critério de contas: minúsculas)."""
    if not BotsRanqueadosAtivos():
        return None
    NickNorm = Nick.strip().lower()[:20]
    if len(NickNorm) < 3:
        return None
    for B in BOTS:
        if B.Nick.lower() == NickNorm:
            return B
    return None


def NickExibicaoPorId(Id: str | None) -> str | None:
    """Resolve id de oponente (conta ou bot) para nick público."""
    if not Id:
        return None
    IdStr = str(Id)
    IdBot = _IdBotInterno(IdStr)
    if IdBot:
        B = ObterBot(IdBot)
        return B.Nick if B else None
    from . import persistencia

    Conta = persistencia.ObterContaPorId(IdStr)
    return Conta["nick"] if Conta else None


def IdBotParaHistorico(IdJogador: str | None) -> str | None:
    """Normaliza id de jogador na sala (bot-xxx) para id gravado no histórico."""
    if not IdJogador:
        return None
    return _IdBotInterno(IdJogador)


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
        and PontosBotAtual(B.Id) <= RP_MAXIMO_BOTS
        and EloDePontos(PontosBotAtual(B.Id)) in ELOS_COM_BOTS
    ]
    if not Livres:
        return None
    EloJogador = EloDePontos(PontosJogador)
    Proximos = sorted(
        Livres, key=lambda B: abs(PontosBotAtual(B.Id) - PontosJogador)
    )
    JanelaRp = JanelaRpBot(PontosJogador, SegundosEspera)
    Janela = [
        B for B in Proximos if abs(PontosBotAtual(B.Id) - PontosJogador) <= JanelaRp
    ]
    MesmoElo = [
        B
        for B in (Janela or Proximos)
        if EloDePontos(PontosBotAtual(B.Id)) == EloJogador
    ]
    Pool = (MesmoElo or Janela or Proximos)[:12]
    if not Pool and Proximos:
        Pool = Proximos[:12]
    return random.choice(Pool) if Pool else None


def ListarBotsProximos(Pontos: int, Limite: int = 12) -> list[BotRanqueado]:
    if not BotsRanqueadosAtivos():
        return []
    Livres = [
        B
        for B in BOTS
        if B.Id not in _BotsReservados
        and B.Id not in _BotsEmPartida
        and PontosBotAtual(B.Id) <= RP_MAXIMO_BOTS
        and EloDePontos(PontosBotAtual(B.Id)) in ELOS_COM_BOTS
    ]
    EloJogador = EloDePontos(Pontos)
    Ordenados = sorted(Livres, key=lambda B: abs(PontosBotAtual(B.Id) - Pontos))
    MesmoElo = [
        B for B in Ordenados if EloDePontos(PontosBotAtual(B.Id)) == EloJogador
    ]
    if MesmoElo:
        return MesmoElo[:Limite]
    return Ordenados[:Limite]


def BotParaRanking(B: BotRanqueado, Posicao: int) -> dict:
    Pontos = PontosBotAtual(B.Id)
    Elo = EloDePontos(Pontos)
    Partidas, Vitorias = EstatisticasBot(B.Id)
    return {
        "posicao": Posicao,
        "nick": B.Nick,
        "pontos": Pontos,
        "elo": Elo,
        "eloNome": NomeEloExibicao(Elo),
        "partidas": Partidas,
        "vitorias": Vitorias,
        "ehBot": False,
        "souEu": False,
    }


def PontosBotPorIdJogador(IdJogador: str) -> int:
    IdBot = _IdBotInterno(IdJogador)
    if not IdBot:
        return 1000
    if IdBot in _BOTS_POR_ID:
        return PontosBotAtual(IdBot)
    return 1000
