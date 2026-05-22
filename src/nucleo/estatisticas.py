"""Estatísticas agregadas do jogador."""

from . import persistencia


def ObterEstatisticasJogador(Nick: str) -> dict:
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
    DiariasVencidas = sum(1 for H in HistoricoDiaria if H["venceu"])

    return {
        "nick": NickNorm,
        "partidasRanking": Partidas,
        "vitoriasRanking": Vitorias,
        "taxaVitoria": round(100 * Vitorias / Partidas, 1) if Partidas else 0,
        "distribuicaoTentativas": Distribuicao,
        "diariasRecentes": len(HistoricoDiaria),
        "diariasVencidas": DiariasVencidas,
        "historicoDiaria": HistoricoDiaria,
    }
