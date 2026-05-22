from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import persistencia

persistencia.InicializarBanco()


@dataclass
class RegistroPontuacao:
    NomeJogador: str
    Pontos: int
    Modo: str
    TentativasUsadas: int
    Venceu: bool
    DataHora: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


PontuacaoBaseVitoria = 1000
BonusPorTentativaSobrando = 180
PenalidadePorTentativa = 120
BonusVersus = 350


def CalcularPontuacao(
    Venceu: bool,
    TentativasUsadas: int,
    Modo: str = "solo",
    VenceuVersus: bool = False,
) -> int:
    if not Venceu:
        return 50 if Modo in ("versus", "sala") and TentativasUsadas >= 6 else 0

    TentativasRestantes = max(0, 6 - TentativasUsadas)
    Pontos = PontuacaoBaseVitoria
    Pontos += TentativasRestantes * BonusPorTentativaSobrando
    Pontos -= (TentativasUsadas - 1) * PenalidadePorTentativa
    Pontos = max(100, Pontos)

    if Modo in ("versus", "sala") and VenceuVersus:
        Pontos += BonusVersus

    return Pontos


def RegistrarPontuacao(
    NomeJogador: str,
    Pontos: int,
    Modo: str,
    TentativasUsadas: int,
    Venceu: bool,
    *,
    IdConta: str | None = None,
) -> RegistroPontuacao | None:
    """Ranking casual só para contas registradas (não visitante) e com pontos > 0."""
    Nick = (NomeJogador or "").strip()[:24] or "Anônimo"
    if IdConta:
        Conta = persistencia.ObterContaPorId(IdConta)
        if not Conta or Conta.get("eh_visitante"):
            return None
    elif persistencia.NickEhVisitante(Nick):
        return None
    if Pontos <= 0:
        return None

    Registro = RegistroPontuacao(
        NomeJogador=Nick,
        Pontos=Pontos,
        Modo=Modo,
        TentativasUsadas=TentativasUsadas,
        Venceu=Venceu,
    )
    persistencia.InserirRanking(
        Registro.NomeJogador,
        Registro.Pontos,
        Registro.Modo,
        Registro.TentativasUsadas,
        Registro.Venceu,
        Registro.DataHora,
    )
    return Registro


def ObterRanking(Limite: int = 20) -> list[dict]:
    persistencia.LimparRankingVisitantesEPontosZero()
    Linhas = persistencia.ListarRanking(max(Limite * 4, 40))
    Filtradas: list[dict] = []
    for L in Linhas:
        Nick = L.get("nome_jogador", "")
        if persistencia.NickEhVisitante(Nick):
            continue
        if int(L.get("pontos", 0)) <= 0:
            continue
        Filtradas.append(L)
        if len(Filtradas) >= Limite:
            break
    return Filtradas
