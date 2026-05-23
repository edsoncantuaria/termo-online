"""Estatísticas agregadas do jogador."""

from . import persistencia
from .modos_solo import (
    ModoDesafio,
    ModoDiaria,
    ModoDueto,
    ModoPratica,
    ModoQuarteto,
)

_NOMES_MODO = {
    ModoPratica: "Prática",
    ModoDiaria: "Palavra do dia",
    ModoDueto: "Dueto",
    ModoQuarteto: "Quarteto",
    ModoDesafio: "Desafio",
    "ranqueada": "Ranqueado 1v1",
    "treino_ranqueado": "Treino!",
}

_ORDEM_MODOS = [
    ModoDiaria,
    ModoDueto,
    ModoQuarteto,
    ModoDesafio,
    "ranqueada",
    "treino_ranqueado",
]


def MontarListaPartidasPorModo(
    Contagem: dict[str, dict[str, int]],
    PartidasRanqueadas: int = 0,
    VitoriasRanqueadas: int = 0,
    PartidasTreinoRanqueado: int = 0,
    VitoriasTreinoRanqueado: int = 0,
) -> list[dict]:
    Itens = []
    for Modo in _ORDEM_MODOS:
        if Modo == "ranqueada":
            Partidas = PartidasRanqueadas
            Vitorias = VitoriasRanqueadas
        elif Modo == "treino_ranqueado":
            Partidas = PartidasTreinoRanqueado
            Vitorias = VitoriasTreinoRanqueado
        else:
            Dados = Contagem.get(Modo) or {}
            Partidas = int(Dados.get("partidas") or 0)
            Vitorias = int(Dados.get("vitorias") or 0)
        Itens.append(
            {
                "modo": Modo,
                "nome": _NOMES_MODO.get(Modo, Modo),
                "partidas": Partidas,
                "vitorias": Vitorias,
            }
        )
    return Itens


def ObterEstatisticasJogador(
    Nick: str,
    IdConta: str | None = None,
    Perfil: dict | None = None,
) -> dict:
    NickNorm = Nick.strip()[:24].lower() or "jogador"
    Ranking = persistencia.ListarRanking(200)
    DoNick = [R for R in Ranking if R["nome_jogador"].lower() == NickNorm]

    Vitorias = sum(1 for R in DoNick if R["venceu"])
    Partidas = len(DoNick)
    Distribuicao = {str(I): 0 for I in range(1, 7)}
    for R in DoNick:
        T = min(6, max(1, R["tentativas_usadas"]))
        Distribuicao[str(T)] = Distribuicao.get(str(T), 0) + 1

    HistoricoDiaria = persistencia.ListarHistoricoDiaria(NickNorm, 14)
    if IdConta:
        PorConta = persistencia.ListarHistoricoDiariaPorConta(IdConta, 14)
        if len(PorConta) >= len(HistoricoDiaria):
            HistoricoDiaria = PorConta
    DiariasVencidas = sum(1 for H in HistoricoDiaria if H["venceu"])

    ContagemModos = persistencia.ContarPartidasSoloPorModo(IdConta, NickNorm)
    PartidasRanqueadas = 0
    VitoriasRanqueadas = 0
    PartidasTreinoRanqueado = 0
    VitoriasTreinoRanqueado = 0
    if Perfil and not Perfil.get("ehVisitante"):
        PartidasRanqueadas = int(Perfil.get("partidasRanqueadas") or 0)
        VitoriasRanqueadas = int(Perfil.get("vitoriasRanqueadas") or 0)
        PartidasTreinoRanqueado = int(Perfil.get("partidasTreinoRanqueado") or 0)
        VitoriasTreinoRanqueado = int(Perfil.get("vitoriasTreinoRanqueado") or 0)
    elif IdConta:
        PartidasRanqueadas = persistencia.ContarPartidasRanqueadasConta(IdConta)
        VitoriasRanqueadas = persistencia.ContarVitoriasRanqueadasConta(IdConta)
        PartidasTreinoRanqueado = persistencia.ContarPartidasTreinoRanqueadoConta(IdConta)
        VitoriasTreinoRanqueado = persistencia.ContarVitoriasTreinoRanqueadoConta(IdConta)

    PartidasPorModo = MontarListaPartidasPorModo(
        ContagemModos,
        PartidasRanqueadas,
        VitoriasRanqueadas,
        PartidasTreinoRanqueado,
        VitoriasTreinoRanqueado,
    )
    _ModosArena = {"ranqueada", "treino_ranqueado"}
    TotalSolo = sum(I["partidas"] for I in PartidasPorModo if I["modo"] not in _ModosArena)

    return {
        "nick": NickNorm,
        "partidasRanking": Partidas,
        "vitoriasRanking": Vitorias,
        "taxaVitoria": round(100 * Vitorias / Partidas, 1) if Partidas else 0,
        "distribuicaoTentativas": Distribuicao,
        "diariasRecentes": len(HistoricoDiaria),
        "diariasVencidas": DiariasVencidas,
        "historicoDiaria": HistoricoDiaria,
        "partidasPorModo": PartidasPorModo,
        "totalPartidasSolo": TotalSolo,
    }
