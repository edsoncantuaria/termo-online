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
) -> RegistroPontuacao:
    Registro = RegistroPontuacao(
        NomeJogador=NomeJogador[:24] or "Anônimo",
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
    return persistencia.ListarRanking(Limite)
