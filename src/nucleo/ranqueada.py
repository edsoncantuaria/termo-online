"""Sistema ranqueado — pontos e elos calculados somente no servidor."""

from dataclasses import dataclass

from . import persistencia

# (id, mínimo inclusive, máximo inclusive)
ELOS = (
    ("madeira", 0, 399),
    ("papelao", 400, 799),
    ("ferro", 800, 1199),
    ("bronze", 1200, 1599),
    ("ouro", 1600, 1999),
    ("platina", 2000, 2399),
    ("diamante", 2400, 2799),
    ("estrela", 2800, 99999),
)

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
    return EloId.replace("_", " ").capitalize()


def CalcularDelta(PontosJogador: int, PontosOponente: int, Venceu: bool) -> int:
    """Vitória: +16 a +20; derrota: -8 a -12, conforme diferença de rating."""
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

    Ativos = [
        J for J in Sala.Jogadores.values() if not J.Espectador
    ]
    Reais = [J for J in Ativos if getattr(J, "IdConta", None) and not getattr(J, "EhBot", False)]
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
