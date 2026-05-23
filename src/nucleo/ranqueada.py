"""Sistema ranqueado — pontos, elos e exibição (somente no servidor)."""

from dataclasses import dataclass

from . import persistencia

# (id, mínimo inclusive, máximo inclusive)
ELOS = (
    ("papelao", 0, 399),
    ("madeira", 400, 799),
    ("ferro", 800, 1199),
    ("bronze", 1200, 1599),
    ("prata", 1600, 1999),
    ("ouro", 2000, 2399),
    ("platina", 2400, 2799),
    ("diamante", 2800, 3199),
    ("estrela", 3200, 99999),
)

NOMES_ELO: dict[str, str] = {
    "papelao": "Papelão",
    "madeira": "Madeira",
    "ferro": "Ferro",
    "bronze": "Bronze",
    "prata": "Prata",
    "ouro": "Ouro",
    "platina": "Platina",
    "diamante": "Diamante",
    "estrela": "Estrela",
}

# Cores para UI (salas online, fila, perfil)
CORES_ELO: dict[str, dict[str, str]] = {
    "papelao": {
        "fundo": "linear-gradient(135deg, #6b5344 0%, #4a3828 100%)",
        "texto": "#f5e6d3",
        "borda": "rgba(180, 140, 90, 0.55)",
        "brilho": "0 0 12px rgba(120, 90, 50, 0.35)",
    },
    "madeira": {
        "fundo": "linear-gradient(135deg, #8b5a2b 0%, #5c3d1e 100%)",
        "texto": "#ffe8c8",
        "borda": "rgba(210, 150, 80, 0.5)",
        "brilho": "0 0 14px rgba(160, 100, 40, 0.4)",
    },
    "ferro": {
        "fundo": "linear-gradient(135deg, #8a939e 0%, #5a626c 100%)",
        "texto": "#eef2f6",
        "borda": "rgba(180, 190, 200, 0.45)",
        "brilho": "0 0 10px rgba(140, 150, 160, 0.35)",
    },
    "bronze": {
        "fundo": "linear-gradient(135deg, #c97b3d 0%, #8b4513 100%)",
        "texto": "#fff4e6",
        "borda": "rgba(230, 160, 80, 0.55)",
        "brilho": "0 0 16px rgba(200, 120, 40, 0.45)",
    },
    "prata": {
        "fundo": "linear-gradient(135deg, #e8ecef 0%, #9aa3ad 50%, #c5cdd6 100%)",
        "texto": "#1a2230",
        "borda": "rgba(220, 228, 235, 0.7)",
        "brilho": "0 0 18px rgba(200, 210, 225, 0.5)",
    },
    "ouro": {
        "fundo": "linear-gradient(135deg, #ffe566 0%, #d4a017 45%, #b8860b 100%)",
        "texto": "#2a1f08",
        "borda": "rgba(255, 220, 100, 0.65)",
        "brilho": "0 0 20px rgba(255, 200, 60, 0.55)",
    },
    "platina": {
        "fundo": "linear-gradient(135deg, #f0f8ff 0%, #7eb8da 40%, #4a7fa8 100%)",
        "texto": "#0d1a28",
        "borda": "rgba(180, 220, 255, 0.6)",
        "brilho": "0 0 22px rgba(120, 180, 255, 0.5)",
    },
    "diamante": {
        "fundo": "linear-gradient(135deg, #e0ffff 0%, #5ec8e8 35%, #2a8fc4 70%, #7b68ee 100%)",
        "texto": "#061820",
        "borda": "rgba(150, 230, 255, 0.7)",
        "brilho": "0 0 24px rgba(100, 200, 255, 0.6)",
    },
    "estrela": {
        "fundo": "linear-gradient(135deg, #fff9c4 0%, #ffd54f 25%, #ff6f00 55%, #7b1fa2 100%)",
        "texto": "#fffef5",
        "borda": "rgba(255, 220, 120, 0.75)",
        "brilho": "0 0 28px rgba(255, 180, 50, 0.65), 0 0 40px rgba(180, 80, 255, 0.35)",
    },
}

ROTULO_SEM_RANK = "Sem Rank"
CLASSE_SEM_RANK = "elo-pill--sem-rank"

PONTOS_INICIAIS = 0
DELTA_VITORIA_MIN = 16
DELTA_VITORIA_MAX = 20
DELTA_DERROTA_MIN = 8
DELTA_DERROTA_MAX = 12


@dataclass
class ResultadoRanqueada:
    IdConta: str
    Nick: str
    PontosAntes: int
    PontosDepois: int
    Delta: int
    EloAntes: str
    EloDepois: str
    Venceu: bool


def EloDePontos(Pontos: int) -> str:
    P = max(0, int(Pontos))
    for Id, Minimo, Maximo in ELOS:
        if Minimo <= P <= Maximo:
            return Id
    return ELOS[-1][0]


def NomeEloExibicao(EloId: str) -> str:
    return NOMES_ELO.get(EloId, EloId.replace("_", " ").capitalize())


def ClasseCssElo(EloId: str | None) -> str:
    if not EloId:
        return CLASSE_SEM_RANK
    return f"elo-pill--{EloId}"


def RotuloRankConta(PartidasRanqueadas: int, Pontos: int) -> str:
    if int(PartidasRanqueadas) <= 0:
        return ROTULO_SEM_RANK
    return NomeEloExibicao(EloDePontos(Pontos))


def MontarCamposRankExibicao(PartidasRanqueadas: int, Pontos: int) -> dict:
    SemRank = int(PartidasRanqueadas) <= 0
    Elo = None if SemRank else EloDePontos(Pontos)
    return {
        "rotuloRank": ROTULO_SEM_RANK if SemRank else NomeEloExibicao(Elo),
        "semRank": SemRank,
        "elo": Elo,
        "eloNome": ROTULO_SEM_RANK if SemRank else NomeEloExibicao(Elo),
        "eloClasse": ClasseCssElo(Elo),
        "pontosRanqueada": int(Pontos),
    }


def MetadadosEloApi(EloId: str) -> dict:
    Cores = CORES_ELO.get(EloId, {})
    return {
        "id": EloId,
        "nome": NomeEloExibicao(EloId),
        "classeCss": ClasseCssElo(EloId),
        **Cores,
    }


def ListarElosApi() -> list[dict]:
    return [
        {**MetadadosEloApi(E[0]), "minimo": E[1], "maximo": E[2]} for E in ELOS
    ]


def MetadadosRankJogadorSala(Jogador) -> dict:
    """Rank/elo para exibir em salas online (arena, desafio, ranqueada)."""
    if getattr(Jogador, "EhBot", False):
        from .bots_ranqueados import PontosBotPorIdJogador

        Pontos = PontosBotPorIdJogador(Jogador.IdJogador)
        Elo = EloDePontos(Pontos)
        return {
            **MontarCamposRankExibicao(1, Pontos),
            "rotuloRank": NomeEloExibicao(Elo),
            "semRank": False,
        }
    IdConta = getattr(Jogador, "IdConta", None)
    if IdConta:
        Conta = persistencia.ObterContaPorId(IdConta)
        if Conta and not Conta.get("eh_visitante"):
            return MontarCamposRankExibicao(
                int(Conta.get("partidas_ranqueadas", 0)),
                int(Conta.get("pontos_ranqueada", 0)),
            )
    return MontarCamposRankExibicao(0, 0)


def CalcularDelta(PontosJogador: int, PontosOponente: int, Venceu: bool) -> int:
    Diff = int(PontosOponente) - int(PontosJogador)
    if Venceu:
        Bonus = max(0, min(DELTA_VITORIA_MAX - DELTA_VITORIA_MIN, Diff // 25))
        return DELTA_VITORIA_MIN + Bonus
    Penal = max(0, min(DELTA_DERROTA_MAX - DELTA_DERROTA_MIN, (-Diff) // 25))
    return -(DELTA_DERROTA_MIN + Penal)


def AplicarDeltaConta(IdConta: str, Delta: int) -> tuple[int, int]:
    Conta = persistencia.ObterContaPorId(IdConta)
    if not Conta:
        raise ValueError("Conta inválida.")
    Antes = int(Conta["pontos_ranqueada"])
    Depois = max(0, Antes + Delta)
    persistencia.AtualizarPontosRanqueada(IdConta, Depois)
    return Antes, Depois


def RegistrarDueloRanqueado(
    IdContaVencedor: str,
    IdContaPerdedor: str,
    CodigoSala: str | None = None,
    IdPartida: str | None = None,
) -> list[ResultadoRanqueada]:
    if IdContaVencedor == IdContaPerdedor:
        raise ValueError("Duelo inválido.")
    Cv = persistencia.ObterContaPorId(IdContaVencedor)
    Cp = persistencia.ObterContaPorId(IdContaPerdedor)
    if not Cv or not Cp:
        raise ValueError("Conta não encontrada.")
    if Cv.get("eh_visitante") or Cp.get("eh_visitante"):
        raise ValueError("Visitantes não pontuam no ranqueado.")

    Pv, Pp = int(Cv["pontos_ranqueada"]), int(Cp["pontos_ranqueada"])
    Dv = CalcularDelta(Pv, Pp, True)
    Dp = CalcularDelta(Pp, Pv, False)
    Av, Nv = AplicarDeltaConta(IdContaVencedor, Dv)
    Ap, Np = AplicarDeltaConta(IdContaPerdedor, Dp)

    persistencia.RegistrarHistoricoRanqueada(
        IdContaVencedor,
        IdContaPerdedor,
        CodigoSala,
        Dv,
        Av,
        Nv,
        True,
        IdPartida,
    )
    persistencia.RegistrarHistoricoRanqueada(
        IdContaPerdedor,
        IdContaVencedor,
        CodigoSala,
        Dp,
        Ap,
        Np,
        False,
        IdPartida,
    )

    return [
        ResultadoRanqueada(
            IdConta=IdContaVencedor,
            Nick=Cv["nick"],
            PontosAntes=Av,
            PontosDepois=Nv,
            Delta=Dv,
            EloAntes=EloDePontos(Av),
            EloDepois=EloDePontos(Nv),
            Venceu=True,
        ),
        ResultadoRanqueada(
            IdConta=IdContaPerdedor,
            Nick=Cp["nick"],
            PontosAntes=Ap,
            PontosDepois=Np,
            Delta=Dp,
            EloAntes=EloDePontos(Ap),
            EloDepois=EloDePontos(Np),
            Venceu=False,
        ),
    ]


def RegistrarDueloRanqueadoVsBot(
    IdContaReal: str,
    VenceuReal: bool,
    PontosBot: int,
    CodigoSala: str | None = None,
    IdPartida: str | None = None,
) -> list[ResultadoRanqueada]:
    Conta = persistencia.ObterContaPorId(IdContaReal)
    if not Conta or Conta.get("eh_visitante"):
        raise ValueError("Conta inválida para ranqueado.")
    Pv = int(Conta["pontos_ranqueada"])
    Delta = CalcularDelta(Pv, int(PontosBot), VenceuReal)
    Antes, Depois = AplicarDeltaConta(IdContaReal, Delta)
    persistencia.RegistrarHistoricoRanqueada(
        IdContaReal,
        None,
        CodigoSala,
        Delta,
        Antes,
        Depois,
        VenceuReal,
        IdPartida,
    )
    return [
        ResultadoRanqueada(
            IdConta=IdContaReal,
            Nick=Conta["nick"],
            PontosAntes=Antes,
            PontosDepois=Depois,
            Delta=Delta,
            EloAntes=EloDePontos(Antes),
            EloDepois=EloDePontos(Depois),
            Venceu=VenceuReal,
        )
    ]


def ProcessarFimSalaRanqueada(Sala) -> list[ResultadoRanqueada] | None:
    if not getattr(Sala.Configuracao, "Ranqueada", False):
        return None
    if not Sala.VencedorId or Sala.VencedorId not in Sala.Jogadores:
        return None

    Ativos = [J for J in Sala.Jogadores.values() if not J.Espectador]
    Reais = [
        J for J in Ativos if getattr(J, "IdConta", None) and not getattr(J, "EhBot", False)
    ]
    Bots = [J for J in Ativos if getattr(J, "EhBot", False)]

    if len(Reais) == 1 and len(Bots) == 1:
        from .bots_ranqueados import PontosBotPorIdJogador

        Real = Reais[0]
        Bot = Bots[0]
        PontosBot = PontosBotPorIdJogador(Bot.IdJogador)
        VenceuReal = Sala.VencedorId == Real.IdJogador
        return RegistrarDueloRanqueadoVsBot(
            Real.IdConta,
            VenceuReal,
            PontosBot,
            Sala.CodigoSala,
            getattr(Sala, "IdPartida", None),
        )

    if len(Reais) != 2:
        return None

    Vencedor = Sala.Jogadores[Sala.VencedorId]
    Perdedor = next(J for J in Reais if J.IdJogador != Sala.VencedorId)
    if Vencedor.IdJogador not in {J.IdJogador for J in Reais}:
        return None

    return RegistrarDueloRanqueado(
        Vencedor.IdConta,
        Perdedor.IdConta,
        Sala.CodigoSala,
        getattr(Sala, "IdPartida", None),
    )
