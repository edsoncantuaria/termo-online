"""Datas no fuso de Brasília (palavra do dia, cap de XP, metas semanais)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

_FUSO_BR = timezone(timedelta(hours=-3))


def AgoraBrasil() -> datetime:
    return datetime.now(_FUSO_BR)


def DataHojeBrasil() -> date:
    return AgoraBrasil().date()


def DataHojeIsoBrasil() -> str:
    return DataHojeBrasil().isoformat()


def SemanaIsoBrasil() -> str:
    """Chave ISO da semana (ano + Wnn) no calendário de Brasília."""
    D = DataHojeBrasil()
    Ano, Semana, _ = D.isocalendar()
    return f"{Ano}-W{Semana:02d}"
