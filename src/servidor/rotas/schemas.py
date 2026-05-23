from typing import Literal

from pydantic import BaseModel, Field

from nucleo.arena_rodadas import ModoPontos, ModoVitorias
from nucleo.gerenciador_salas import (
    MaximoCaracteresSenha,
    MaximoJogadoresPermitido,
    MinimoJogadoresSala,
    TempoLimiteMaximoSegundos,
)
from nucleo.logica_jogo import ModoPratica
from nucleo.modos_solo import DificuldadeNormal
from servidor.estado_global import GerenciadorVersus


class IniciarJogoRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)
    modo: Literal["diaria", "pratica", "dueto", "quarteto", "desafio"] = ModoPratica
    dificuldade: Literal["normal", "dificil"] = DificuldadeNormal
    codigoDesafio: str | None = Field(default=None, max_length=8)


class IniciarSoloRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)


class ChuteSoloRequest(BaseModel):
    idPartida: str
    palavra: str
    nomeJogador: str = Field(default="Jogador", max_length=24)
    tokenPartida: str | None = Field(default=None, max_length=64)


class CriarSalaRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)
    mesmaPalavra: bool = False
    verOutros: bool = True
    maximoJogadores: int = Field(
        default=4, ge=MinimoJogadoresSala, le=MaximoJogadoresPermitido
    )
    senha: str | None = Field(default=None, max_length=MaximoCaracteresSenha)
    tempoLimiteSegundos: int = Field(default=180, ge=0, le=TempoLimiteMaximoSegundos)
    numeroRodadas: int = Field(default=0, ge=0, le=100)
    modoSessao: str = Field(default=ModoVitorias)
    metaVitorias: int = Field(default=3, ge=1, le=20)
    inicioAutoDois: bool = False
    salaPublica: bool = True


class EntrarSalaRequest(BaseModel):
    codigoSala: str = Field(min_length=6, max_length=6)
    nomeJogador: str = Field(default="Jogador", max_length=24)
    senha: str | None = Field(default=None, max_length=MaximoCaracteresSenha)
    espectador: bool = False


class SairSalaRequest(BaseModel):
    codigoSala: str = Field(min_length=6, max_length=6)
    idJogador: str


class DesistirPartidaRequest(BaseModel):
    idJogador: str
    tokenSessao: str = Field(min_length=8, max_length=64)


class GradeDiariaRequest(BaseModel):
    nick: str = Field(max_length=24)
    gradeTexto: str = ""
    venceu: bool = False
    tentativasUsadas: int = Field(ge=1, le=6)
    pontos: int = Field(default=0, ge=0)


class AuthLoginRequest(BaseModel):
    identificador: str = Field(min_length=3, max_length=120)
    senha: str = Field(min_length=6, max_length=64)


class AuthRegistroRequest(BaseModel):
    nick: str = Field(min_length=3, max_length=20)
    email: str = Field(min_length=5, max_length=120)
    senha: str = Field(min_length=6, max_length=64)


class AuthVisitanteRequest(BaseModel):
    nick: str | None = Field(default=None, min_length=3, max_length=20)


def MontarRespostaSala(Sala, Jogador) -> dict:
    from nucleo.partida_sessao import GarantirIdPartidaSala, GarantirTokenJogador

    GarantirIdPartidaSala(Sala)
    GarantirTokenJogador(Jogador)
    Resposta = GerenciadorVersus.EstadoPublicoSala(Sala, Jogador.IdJogador)
    Resposta["idJogador"] = Jogador.IdJogador
    Resposta["nomeJogador"] = Jogador.NomeJogador
    if getattr(Jogador, "TokenSessao", None):
        Resposta["tokenSessao"] = Jogador.TokenSessao
    return Resposta
