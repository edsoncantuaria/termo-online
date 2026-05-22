"""XP, níveis infinitos, badges e recompensas (somente conta logada)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from . import persistencia

# —— XP por ação (conta registrada) ——
XP_DIARIA_TENTATIVA = 10
XP_DIARIA_ACERTO = 35
XP_DIARIA_CONCLUIR = 20
XP_PRATICA_CHUTE = 4
XP_PRATICA_VITORIA = 15
XP_ARENA_RODADA = 14
XP_RANQUEADA_PARTIDA = 45
XP_RANQUEADA_VITORIA_EXTRA = 20

# Ganho efetivo: 100% no nível 1, decai até ~15%; teto diário alto (anti-farm).
CAP_XP_DIARIO = 2200
XP_MULTIPLICADOR_PISO = 0.15
XP_MULTIPLICADOR_DECAIMENTO = 0.048

BADGES: tuple[dict, ...] = (
    {
        "id": "primeiro_passo",
        "nome": "Primeiro passo",
        "descricao": "Ganhou XP pela primeira vez.",
        "icone": "🌱",
    },
    {
        "id": "diaria_tentou",
        "nome": "No jogo",
        "descricao": "Enviou a primeira tentativa na palavra do dia.",
        "icone": "📅",
    },
    {
        "id": "diaria_venceu",
        "nome": "Palavra do dia",
        "descricao": "Acertou a palavra do dia.",
        "icone": "⭐",
    },
    {
        "id": "diaria_persistente",
        "nome": "Teimoso",
        "descricao": "Concluiu a diária sem acertar (6 tentativas).",
        "icone": "💪",
    },
    {
        "id": "nivel_5",
        "nome": "Nível 5",
        "descricao": "Alcançou o nível 5.",
        "icone": "⑤",
    },
    {
        "id": "nivel_10",
        "nome": "Nível 10",
        "descricao": "Alcançou o nível 10 — borda bronze.",
        "icone": "⑩",
    },
    {
        "id": "nivel_25",
        "nome": "Nível 25",
        "descricao": "Alcançou o nível 25.",
        "icone": "✦",
    },
    {
        "id": "nivel_50",
        "nome": "Nível 50",
        "descricao": "Alcançou o nível 50 — lenda.",
        "icone": "👑",
    },
    {
        "id": "ranqueada_1",
        "nome": "Duelista",
        "descricao": "Concluiu o primeiro duelo ranqueado.",
        "icone": "⚔",
    },
    {
        "id": "ranqueada_venceu",
        "nome": "Vitória ranqueada",
        "descricao": "Venceu um duelo ranqueado.",
        "icone": "🏆",
    },
)

_BADGES_POR_ID = {B["id"]: B for B in BADGES}

FAIXAS_NIVEL = (
    {"nome": "Iniciante", "cor1": "#9d96ad", "cor2": "#5c5668", "borda": 2},
    {"nome": "Bronze", "cor1": "#cd9b5a", "cor2": "#7a5520", "borda": 3},
    {"nome": "Prata", "cor1": "#c8d4e0", "cor2": "#6a7a8a", "borda": 3},
    {"nome": "Ouro", "cor1": "#f0d078", "cor2": "#a88632", "borda": 4},
    {"nome": "Platina", "cor1": "#b8f0e8", "cor2": "#3a8a7a", "borda": 4},
    {"nome": "Diamante", "cor1": "#d4b8ff", "cor2": "#6b3f9a", "borda": 5},
    {"nome": "Estrela", "cor1": "#ffb8d4", "cor2": "#9a3060", "borda": 5},
    {"nome": "Mítico", "cor1": "#fff0a8", "cor2": "#c9a030", "borda": 6},
    {"nome": "Lenda", "cor1": "#ffffff", "cor2": "#c9b458", "borda": 7},
    {"nome": "Transcendente", "cor1": "#e8f4ff", "cor2": "#5fad62", "borda": 8},
)


@dataclass
class EstadoNivel:
    Nivel: int
    XpTotal: int
    XpNoNivel: int
    XpProximoNivel: int


def MultiplicadorXpGanho(Nivel: int) -> float:
    """Quanto do XP base entra na conta (1.0 no início, piso ~15% em níveis altos)."""
    N = max(1, int(Nivel))
    Mult = 1.0 / (1.0 + (N - 1) * XP_MULTIPLICADOR_DECAIMENTO)
    return max(XP_MULTIPLICADOR_PISO, Mult)


def XpBrutoParaEfetivo(Nivel: int, XpBruto: int) -> int:
    if XpBruto <= 0:
        return 0
    return max(1, int(round(XpBruto * MultiplicadorXpGanho(Nivel))))


def XpParaSubirNivel(Nivel: int) -> int:
    """XP para subir de N→N+1: barato no início, bem mais caro depois."""
    N = max(1, int(Nivel))
    return 50 + (N - 1) * 16 + ((N - 1) // 10) * 40 + ((N - 1) // 25) * 55


def CalcularEstadoNivel(XpTotal: int) -> EstadoNivel:
    Xp = max(0, int(XpTotal))
    Nivel = 1
    Restante = Xp
    while True:
        Custo = XpParaSubirNivel(Nivel)
        if Restante < Custo:
            return EstadoNivel(
                Nivel=Nivel,
                XpTotal=Xp,
                XpNoNivel=Restante,
                XpProximoNivel=Custo,
            )
        Restante -= Custo
        Nivel += 1


def EstiloNivel(Nivel: int) -> dict:
    Faixa = min((max(1, Nivel) - 1) // 10, len(FAIXAS_NIVEL) - 1)
    Base = FAIXAS_NIVEL[Faixa]
    return {
        "faixa": Faixa,
        "faixaNome": Base["nome"],
        "cor1": Base["cor1"],
        "cor2": Base["cor2"],
        "bordaPx": Base["borda"],
    }


def MontarProgressoConta(IdConta: str) -> dict:
    Xp = persistencia.ObterXpConta(IdConta)
    Estado = CalcularEstadoNivel(Xp)
    BadgesIds = persistencia.ListarBadgesConta(IdConta)
    Badges = []
    for Bid in BadgesIds:
        Def = _BADGES_POR_ID.get(Bid)
        if Def:
            Badges.append({**Def, "desbloqueada": True})
    for Def in BADGES:
        if Def["id"] not in BadgesIds:
            Badges.append({**Def, "desbloqueada": False})
    Estilo = EstiloNivel(Estado.Nivel)
    Hoje = persistencia.ObterXpGanhoDiario(IdConta)
    Mult = MultiplicadorXpGanho(Estado.Nivel)
    return {
        "xpTotal": Estado.XpTotal,
        "nivel": Estado.Nivel,
        "xpNoNivel": Estado.XpNoNivel,
        "xpProximoNivel": Estado.XpProximoNivel,
        "progressoPct": round(100 * Estado.XpNoNivel / max(1, Estado.XpProximoNivel)),
        "estiloNivel": Estilo,
        "badges": Badges,
        "badgesDesbloqueadas": len(BadgesIds),
        "badgesTotal": len(BADGES),
        "xpGanhoHoje": Hoje,
        "xpCapDiario": CAP_XP_DIARIO,
        "xpRestanteHoje": max(0, CAP_XP_DIARIO - Hoje),
        "multiplicadorXpPct": round(100 * Mult),
    }


def _ConcederXp(IdConta: str, QuantidadeBruta: int, Motivo: str) -> dict | None:
    if QuantidadeBruta <= 0:
        return None
    Antes = persistencia.ObterXpConta(IdConta)
    NvAntes = CalcularEstadoNivel(Antes).Nivel
    Efetivo = XpBrutoParaEfetivo(NvAntes, QuantidadeBruta)
    DataHoje = date.today().isoformat()
    GanhoHoje = persistencia.ObterXpGanhoDiario(IdConta, DataHoje)
    RestanteCap = max(0, CAP_XP_DIARIO - GanhoHoje)
    if RestanteCap <= 0:
        return {
            "xpGanho": 0,
            "xpBruto": QuantidadeBruta,
            "xpCapAtingido": True,
            "motivo": Motivo,
            "xpTotal": Antes,
            "nivel": NvAntes,
            "subiuNivel": False,
            "novasBadges": [],
            "progresso": MontarProgressoConta(IdConta),
        }
    Efetivo = min(Efetivo, RestanteCap)
    Depois = persistencia.AdicionarXpConta(IdConta, Efetivo)
    persistencia.RegistrarXpGanhoDiario(IdConta, Efetivo, DataHoje)
    NvDepois = CalcularEstadoNivel(Depois).Nivel
    persistencia.RegistrarLogXp(IdConta, Efetivo, Motivo)
    NovasBadges = _AvaliarBadges(IdConta, NvDepois=NvDepois)
    return {
        "xpGanho": Efetivo,
        "xpBruto": QuantidadeBruta,
        "xpCapAtingido": GanhoHoje + Efetivo >= CAP_XP_DIARIO,
        "motivo": Motivo,
        "xpTotal": Depois,
        "nivel": NvDepois,
        "subiuNivel": NvDepois > NvAntes,
        "novasBadges": NovasBadges,
        "progresso": MontarProgressoConta(IdConta),
    }


def _AvaliarBadges(IdConta: str, NvDepois: int | None = None) -> list[dict]:
    if NvDepois is None:
        NvDepois = CalcularEstadoNivel(persistencia.ObterXpConta(IdConta)).Nivel
    Novas: list[dict] = []
    Regras = (
        ("nivel_5", NvDepois >= 5),
        ("nivel_10", NvDepois >= 10),
        ("nivel_25", NvDepois >= 25),
        ("nivel_50", NvDepois >= 50),
    )
    for Bid, Ok in Regras:
        if Ok and persistencia.DesbloquearBadge(IdConta, Bid):
            Novas.append(_BADGES_POR_ID[Bid])
    Partidas = persistencia.ContarPartidasRanqueadasConta(IdConta)
    if Partidas >= 1 and persistencia.DesbloquearBadge(IdConta, "ranqueada_1"):
        Novas.append(_BADGES_POR_ID["ranqueada_1"])
    Vitorias = persistencia.ContarVitoriasRanqueadasConta(IdConta)
    if Vitorias >= 1 and persistencia.DesbloquearBadge(IdConta, "ranqueada_venceu"):
        Novas.append(_BADGES_POR_ID["ranqueada_venceu"])
    return Novas


def DesbloquearBadgeSe(IdConta: str, BadgeId: str) -> dict | None:
    if persistencia.DesbloquearBadge(IdConta, BadgeId):
        return _BADGES_POR_ID.get(BadgeId)
    return None


def RecompensaDiariaChute(
    IdConta: str,
    DataDia: str,
    IdPartida: str,
    IndiceTentativa: int,
    Acertou: bool,
    Encerrada: bool,
    Venceu: bool,
) -> dict | None:
    if not persistencia.RegistrarXpDiariaTentativa(
        IdConta, DataDia, IdPartida, IndiceTentativa
    ):
        return None
    Total = XP_DIARIA_TENTATIVA
    Motivo = "diaria_tentativa"
    if Acertou:
        Total += XP_DIARIA_ACERTO
        Motivo = "diaria_acerto"
    Resultado = _ConcederXp(IdConta, Total, Motivo)
    if Resultado:
        DesbloquearBadgeSe(IdConta, "diaria_tentou")
        if not persistencia.JaDesbloqueouBadge(IdConta, "primeiro_passo"):
            DesbloquearBadgeSe(IdConta, "primeiro_passo")
    if Encerrada and persistencia.MarcarDiariaXpConclusao(IdConta, DataDia):
        Extra = _ConcederXp(IdConta, XP_DIARIA_CONCLUIR, "diaria_concluir")
        if Venceu:
            DesbloquearBadgeSe(IdConta, "diaria_venceu")
        else:
            DesbloquearBadgeSe(IdConta, "diaria_persistente")
        return Extra or Resultado
    return Resultado


def RecompensaPraticaChute(IdConta: str, Encerrada: bool, Venceu: bool) -> dict | None:
    Total = XP_PRATICA_CHUTE
    Motivo = "pratica_chute"
    if Encerrada and Venceu:
        Total += XP_PRATICA_VITORIA
        Motivo = "pratica_vitoria"
    return _ConcederXp(IdConta, Total, Motivo)


def RecompensaRanqueada(IdConta: str, Venceu: bool) -> dict | None:
    Total = XP_RANQUEADA_PARTIDA
    if Venceu:
        Total += XP_RANQUEADA_VITORIA_EXTRA
    return _ConcederXp(IdConta, Total, "ranqueada_partida")
