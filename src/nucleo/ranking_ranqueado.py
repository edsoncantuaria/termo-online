"""Ranking unificado: contas reais + comunidade ativa (bots + base passiva)."""

from __future__ import annotations

import hashlib
import random

from . import persistencia
from .bots_ranqueados import BOTS
from .ranqueada import EloDePontos, NomeEloExibicao

TOP_EXIBIDO = 20
JANELA_VIZINHOS = 3
POPULACAO_PASSIVA = 2400


def _StatsExibicaoPassivo(Chave: str) -> tuple[int, int]:
    H = int(hashlib.md5(Chave.encode()).hexdigest()[:8], 16)
    Partidas = 8 + (H % 220)
    Vitorias = max(1, Partidas * (30 + (H % 40)) // 100)
    return Partidas, Vitorias


def _GerarPopulacaoPassiva() -> list[dict]:
    Rng = random.Random(77)
    Nomes = (
        "lucas",
        "maria",
        "pedro",
        "julia",
        "theo",
        "lara",
        "enzo",
        "mel",
        "davi",
        "bia",
        "noah",
        "luna",
        "theo",
        "miguel",
        "helena",
        "arthur",
        "alice",
        "bernardo",
        "valentina",
        "gabriel",
        "manu",
        "samuel",
        "clara",
        "benicio",
        "luiza",
    )
    Sufixos = (
        "",
        "br",
        "pro",
        "x",
        "99",
        "777",
        "game",
        "word",
        "pt",
        "oficial",
        "rank",
        "play",
        "win",
        "top",
        "go",
    )
    Vistos: set[str] = set()
    Lista: list[dict] = []
    I = 0
    while len(Lista) < POPULACAO_PASSIVA:
        Nick = (Rng.choice(Nomes) + Rng.choice(Sufixos) + str(Rng.randint(0, 999))).lower()[
            :20
        ]
        if len(Nick) < 3 or Nick in Vistos:
            continue
        Vistos.add(Nick)
        Pontos = int(Rng.betavariate(2.0, 5.0) * 2800)
        Partidas, Vitorias = _StatsExibicaoPassivo(f"pass_{I}")
        Lista.append(
            {
                "nick": Nick,
                "pontos": Pontos,
                "elo": EloDePontos(Pontos),
                "eloNome": NomeEloExibicao(EloDePontos(Pontos)),
                "partidas": Partidas,
                "vitorias": Vitorias,
                "ehBot": True,
            }
        )
        I += 1
    return Lista


_POPULACAO_PASSIVA: list[dict] = _GerarPopulacaoPassiva()


def _StatsExibicaoBot(IdBot: str) -> tuple[int, int]:
    H = int(hashlib.md5(IdBot.encode()).hexdigest()[:8], 16)
    Partidas = 5 + (H % 180)
    Vitorias = max(1, Partidas * (35 + (H % 30)) // 100)
    return Partidas, Vitorias


def _ItemCliente(Posicao: int, E: dict, SouEu: bool) -> dict:
    return {
        "tipo": "jogador",
        "posicao": Posicao,
        "nick": E["nick"],
        "pontos": E["pontos"],
        "elo": E["elo"],
        "eloNome": E["eloNome"],
        "partidas": E["partidas"],
        "vitorias": E["vitorias"],
        "souEu": SouEu,
    }


def _MontarListaExibicao(
    Entradas: list[dict],
    NickEu: str,
    LimiteTopo: int = TOP_EXIBIDO,
    Janela: int = JANELA_VIZINHOS,
) -> tuple[list[dict], int | None]:
    Total = len(Entradas)
    MinhaPosicao: int | None = None
    IndiceEu: int | None = None

    for I, E in enumerate(Entradas):
        if not E["ehBot"] and E["nick"].lower() == NickEu:
            MinhaPosicao = I + 1
            IndiceEu = I
            break

    Resultado: list[dict] = []
    IndicesIncluidos: set[int] = set()

    def IncluirIndice(Idx: int) -> None:
        if Idx < 0 or Idx >= Total or Idx in IndicesIncluidos:
            return
        E = Entradas[Idx]
        SouEu = IndiceEu is not None and Idx == IndiceEu
        Resultado.append(_ItemCliente(Idx + 1, E, SouEu))
        IndicesIncluidos.add(Idx)

    Topo = min(LimiteTopo, Total)
    for Idx in range(Topo):
        IncluirIndice(Idx)

    if IndiceEu is not None and IndiceEu >= LimiteTopo:
        UltimoTopo = Topo - 1
        InicioJanela = max(LimiteTopo, IndiceEu - Janela)
        if InicioJanela > UltimoTopo + 1:
            Resultado.append({"tipo": "ellipsis"})
        FimJanela = min(Total - 1, IndiceEu + Janela)
        for Idx in range(InicioJanela, FimJanela + 1):
            IncluirIndice(Idx)

    return Resultado, MinhaPosicao


def MontarRankingCompleto(
    Perfil: dict | None,
    LimiteTopo: int = TOP_EXIBIDO,
) -> dict:
    Entradas: list[dict] = []

    for Linha in persistencia.ListarContasRanqueamento():
        Pontos = int(Linha["pontos_ranqueada"])
        Elo = EloDePontos(Pontos)
        Entradas.append(
            {
                "nick": Linha["nick"],
                "pontos": Pontos,
                "elo": Elo,
                "eloNome": NomeEloExibicao(Elo),
                "partidas": int(Linha.get("partidas_ranqueadas", 0)),
                "vitorias": int(Linha.get("vitorias_ranqueadas", 0)),
                "ehBot": False,
            }
        )

    from .bots_ranqueados import EstatisticasBot, PontosBotAtual

    for B in BOTS:
        Pontos = PontosBotAtual(B.Id)
        Partidas, Vitorias = EstatisticasBot(B.Id)
        if Partidas <= 0:
            Partidas, Vitorias = _StatsExibicaoBot(B.Id)
        Entradas.append(
            {
                "nick": B.Nick,
                "pontos": Pontos,
                "elo": EloDePontos(Pontos),
                "eloNome": NomeEloExibicao(EloDePontos(Pontos)),
                "partidas": Partidas,
                "vitorias": Vitorias,
                "ehBot": True,
            }
        )

    Entradas.extend(_POPULACAO_PASSIVA)
    Entradas.sort(key=lambda E: (-E["pontos"], E["nick"]))
    Total = len(Entradas)
    NickEu = (Perfil or {}).get("nick", "").lower()

    Ranking, MinhaPosicao = _MontarListaExibicao(Entradas, NickEu, LimiteTopo)

    Eu = Perfil
    if Eu and MinhaPosicao is None and not Eu.get("ehVisitante"):
        Pontos = int(Eu.get("pontosRanqueada", 0))
        MinhaPosicao = sum(1 for E in Entradas if E["pontos"] > Pontos) + 1
        if MinhaPosicao > Total:
            MinhaPosicao = Total
        if MinhaPosicao > LimiteTopo:
            if not any(R.get("tipo") == "ellipsis" for R in Ranking):
                Ranking.append({"tipo": "ellipsis"})
            Ranking.append(
                _ItemCliente(
                    MinhaPosicao,
                    {
                        "nick": Eu.get("nick", ""),
                        "pontos": Pontos,
                        "elo": Eu.get("elo") or EloDePontos(Pontos),
                        "eloNome": Eu.get("eloNome")
                        or NomeEloExibicao(EloDePontos(Pontos)),
                        "partidas": int(Eu.get("partidasRanqueadas", 0)),
                        "vitorias": int(Eu.get("vitoriasRanqueadas", 0)),
                    },
                    True,
                )
            )

    return {
        "ranking": Ranking,
        "eu": Eu,
        "minhaPosicao": MinhaPosicao,
        "totalRanqueados": Total,
        "topExibido": LimiteTopo,
    }
