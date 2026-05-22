"""Metas semanais de progresso (conta registrada)."""

from __future__ import annotations

from . import persistencia
from .progresso import _ConcederXp
from .tempo_brasil import SemanaIsoBrasil

METAS_SEMANAIS: tuple[dict, ...] = (
    {
        "id": "diaria_3",
        "nome": "Palavras da semana",
        "descricao": "Conclua a palavra do dia em 3 dias diferentes nesta semana.",
        "tipo": "diaria_conclusao",
        "meta": 3,
        "xpRecompensa": 90,
    },
    {
        "id": "ranqueada_3",
        "nome": "Duelista ativo",
        "descricao": "Jogue 3 duelos ranqueados nesta semana.",
        "tipo": "ranqueada_partida",
        "meta": 3,
        "xpRecompensa": 120,
    },
    {
        "id": "arena_5",
        "nome": "Na arena",
        "descricao": "Participe de 5 rodadas na arena nesta semana.",
        "tipo": "arena_rodada",
        "meta": 5,
        "xpRecompensa": 80,
    },
)

_METAS_POR_ID = {M["id"]: M for M in METAS_SEMANAIS}


def RegistrarProgressoMeta(IdConta: str, Tipo: str, Quantidade: int = 1) -> list[dict]:
    """Incrementa contadores e concede XP das metas concluídas."""
    Semana = SemanaIsoBrasil()
    Recompensas: list[dict] = []
    for Meta in METAS_SEMANAIS:
        if Meta["tipo"] != Tipo:
            continue
        Novo = persistencia.IncrementarMetaSemanal(
            IdConta, Semana, Meta["id"], Quantidade, Meta["meta"]
        )
        if Novo is None:
            continue
        if Novo >= Meta["meta"] and persistencia.MarcarMetaSemanalRecompensada(
            IdConta, Semana, Meta["id"]
        ):
            R = _ConcederXp(
                IdConta, Meta["xpRecompensa"], f"meta_semanal_{Meta['id']}"
            )
            if R:
                Recompensas.append({**R, "metaId": Meta["id"], "metaNome": Meta["nome"]})
    return Recompensas


def MontarMetasSemanaisConta(IdConta: str) -> list[dict]:
    Semana = SemanaIsoBrasil()
    Progresso = persistencia.ObterProgressoMetasSemana(IdConta, Semana)
    Recompensadas = persistencia.ListarMetasSemanaisRecompensadas(IdConta, Semana)
    Lista: list[dict] = []
    for Meta in METAS_SEMANAIS:
        Atual = Progresso.get(Meta["id"], 0)
        Lista.append(
            {
                "id": Meta["id"],
                "nome": Meta["nome"],
                "descricao": Meta["descricao"],
                "progresso": min(Atual, Meta["meta"]),
                "meta": Meta["meta"],
                "xpRecompensa": Meta["xpRecompensa"],
                "concluida": Atual >= Meta["meta"],
                "recompensada": Meta["id"] in Recompensadas,
            }
        )
    return Lista


def LembreteMetasPendentes(IdConta: str) -> str | None:
    """Texto curto para UI quando falta pouco para concluir uma meta."""
    for Item in MontarMetasSemanaisConta(IdConta):
        if Item["concluida"]:
            continue
        Falta = Item["meta"] - Item["progresso"]
        if 0 < Falta <= 2:
            return f"Falta {Falta} para a meta «{Item['nome']}» esta semana."
    return None
