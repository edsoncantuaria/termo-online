"""Temporadas de ranqueada (calendário mensal, RP exibido com ajuste suave)."""

from datetime import date

from .tempo_brasil import DataHojeBrasil


def IdTemporadaAtual(Data: date | None = None) -> str:
    D = Data or DataHojeBrasil()
    return f"{D.year}-{D.month:02d}"


def MontarInfoTemporada() -> dict:
    D = DataHojeBrasil()
    Id = IdTemporadaAtual(D)
    ProximoMes = D.month % 12 + 1
    AnoProx = D.year + (1 if D.month == 12 else 0)
    return {
        "id": Id,
        "nome": f"Temporada {D.strftime('%B %Y')}",
        "inicio": f"{D.year}-{D.month:02d}-01",
        "proximoReset": f"{AnoProx}-{ProximoMes:02d}-01",
        "descricao": (
            "Ranking e RP seguem a temporada do mês (horário de Brasília). "
            "Partidas e vitórias da temporada são contadas à parte do total da conta."
        ),
    }
