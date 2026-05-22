"""Partidas solo em memória + persistência SQLite."""

import secrets
import uuid
from dataclasses import dataclass, field

from nucleo import persistencia
from nucleo.modos_solo import (
    ContarTentativasGlobais,
    MaximoTentativasModo,
    QuantidadePalavrasModo,
    TabuleirosParaCliente,
)


@dataclass
class PartidaSolo:
    IdPartida: str
    PalavraSecreta: str
    PalavraComAcento: str
    Modo: str = "pratica"
    DataDia: str | None = None
    Tentativas: list[dict] = field(default_factory=list)
    Tabuleiros: list[dict] = field(default_factory=list)
    Dificuldade: str = "normal"
    CodigoDesafio: str | None = None
    Encerrada: bool = False
    Venceu: bool = False
    NomeJogador: str = "Jogador"
    IdConta: str | None = None
    TokenPartida: str | None = None


PartidasSolo: dict[str, PartidaSolo] = {}


def ObterPartida(IdPartida: str) -> PartidaSolo | None:
    if IdPartida not in PartidasSolo:
        Carregada = persistencia.CarregarPartidaSolo(IdPartida, PartidaSolo)
        if Carregada:
            PartidasSolo[IdPartida] = Carregada
    return PartidasSolo.get(IdPartida)


def SalvarPartida(Partida: PartidaSolo) -> None:
    PartidasSolo[Partida.IdPartida] = Partida
    persistencia.SalvarPartidaSolo(Partida)


def MontarRespostaPartida(Partida: PartidaSolo) -> dict:
    MaxTent = MaximoTentativasModo(Partida.Modo)
    Usadas = (
        ContarTentativasGlobais(Partida.Tabuleiros)
        if Partida.Tabuleiros
        else len(Partida.Tentativas)
    )
    return {
        "idPartida": Partida.IdPartida,
        "modo": Partida.Modo,
        "dataDia": Partida.DataDia,
        "dificuldade": Partida.Dificuldade,
        "codigoDesafio": Partida.CodigoDesafio,
        "maximoTentativas": MaxTent,
        "tentativasUsadas": Usadas,
        "encerrada": Partida.Encerrada,
        "venceu": Partida.Venceu,
        "tentativas": Partida.Tentativas,
        "tabuleiros": TabuleirosParaCliente(
            Partida.Tabuleiros,
            RevelarSegredos=Partida.Encerrada,
        ),
        "quantidadePalavras": QuantidadePalavrasModo(Partida.Modo),
        "tokenPartida": Partida.TokenPartida,
    }


def ValidarTokenPartida(Partida: PartidaSolo, TokenEnviado: str | None) -> bool:
    if not Partida.TokenPartida:
        return True
    return bool(TokenEnviado) and TokenEnviado == Partida.TokenPartida


def NovaPartida(
    *,
    PalavraSecreta: str,
    PalavraComAcento: str,
    Modo: str,
    Tabuleiros: list[dict],
    DataDia: str | None = None,
    Dificuldade: str = "normal",
    CodigoDesafio: str | None = None,
    NomeJogador: str = "Jogador",
    IdConta: str | None = None,
) -> PartidaSolo:
    IdPartida = str(uuid.uuid4())
    TokenPartida = secrets.token_urlsafe(16)
    Partida = PartidaSolo(
        IdPartida=IdPartida,
        TokenPartida=TokenPartida,
        PalavraSecreta=PalavraSecreta,
        PalavraComAcento=PalavraComAcento,
        Modo=Modo,
        DataDia=DataDia,
        NomeJogador=NomeJogador,
        Tabuleiros=Tabuleiros,
        Dificuldade=Dificuldade,
        CodigoDesafio=CodigoDesafio,
        IdConta=IdConta,
    )
    SalvarPartida(Partida)
    return Partida
