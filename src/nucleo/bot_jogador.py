"""Simulação de chutes para oponentes bot em duelos ranqueados (ritmo humano ~30s/chute)."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .bots_ranqueados import PontosBotPorIdJogador
from .dicionario import NormalizarPalavra, ObterDicionario, ObterPalavraComAcento, PalavraExisteNoDicionario

INTERVALO_ENTRE_CHUTES_SEG = 30.0

# Perfis (soma 100%): falha 30%, médio 40%, lento 25%, rápido 5%
_PERFIL_FALHA = 0.30
_PERFIL_MEDIO = 0.40
_PERFIL_LENTO = 0.25

_ESTADOS: dict[tuple[str, str], "EstadoBotRodada"] = {}
_RODADA_BOT: dict[str, int] = {}


@dataclass
class EstadoBotRodada:
    Perfil: str
    InicioEpoch: float
    ProximoChuteEpoch: float
    ChuteNumero: int
    TentativaVitoria: int | None


def LimparEstadosBotsSala(CodigoSala: str) -> None:
    Codigo = CodigoSala.upper()
    for Chave in list(_ESTADOS.keys()):
        if Chave[0] == Codigo:
            del _ESTADOS[Chave]
    _RODADA_BOT.pop(Codigo, None)


def _EscolherPerfil() -> tuple[str, int | None]:
    R = random.random()
    if R < _PERFIL_FALHA:
        return "falha", None
    if R < _PERFIL_FALHA + _PERFIL_MEDIO:
        return "medio", random.randint(3, 5)
    if R < _PERFIL_FALHA + _PERFIL_MEDIO + _PERFIL_LENTO:
        return "lento", random.randint(4, 6)
    return "rapido", random.randint(2, 4)


def _GarantirEstado(Sala, Bot) -> EstadoBotRodada:
    Codigo = Sala.CodigoSala.upper()
    Chave = (Codigo, Bot.IdJogador)
    Rodada = Sala.RodadaAtual
    if _RODADA_BOT.get(Codigo) != Rodada or Chave not in _ESTADOS:
        Perfil, Tentativa = _EscolherPerfil()
        Agora = time.time()
        _ESTADOS[Chave] = EstadoBotRodada(
            Perfil=Perfil,
            InicioEpoch=Agora,
            ProximoChuteEpoch=Agora + INTERVALO_ENTRE_CHUTES_SEG,
            ChuteNumero=0,
            TentativaVitoria=Tentativa,
        )
        _RODADA_BOT[Codigo] = Rodada
    return _ESTADOS[Chave]


def _FiltrarPorFeedback(Candidatos: list[str], Tentativas: list[dict]) -> list[str]:
    if not Tentativas:
        return Candidatos
    Ultima = Tentativas[-1]
    Letras = Ultima.get("letras") or list(Ultima.get("palavra", ""))
    Estados = Ultima.get("estados") or []
    if len(Letras) != len(Estados):
        return Candidatos

    Verdes: dict[int, str] = {}
    Cinzas: set[str] = set()

    for I, (L, E) in enumerate(zip(Letras, Estados)):
        Ln = str(L).lower()
        if E == "correto":
            Verdes[I] = Ln
        elif E == "ausente":
            Cinzas.add(Ln)

    Filtradas: list[str] = []
    for Palavra in Candidatos:
        if len(Palavra) != 5:
            continue
        Ok = True
        for Pos, Letra in Verdes.items():
            if Palavra[Pos] != Letra:
                Ok = False
                break
        if not Ok:
            continue
        for Letra in Cinzas:
            if Letra not in Verdes.values() and Palavra.count(Letra) > 0:
                Ok = False
                break
        if Ok:
            Filtradas.append(Palavra)
    return Filtradas or Candidatos


def EscolherPalavraChute(Jogador, PalavraSecreta: str, Estado: EstadoBotRodada) -> str | None:
    _, SemAcento, _ = ObterDicionario()
    Tentadas = {
        t.get("palavra", "").lower()
        for t in Jogador.Tentativas
        if t.get("palavra")
    }
    Candidatos = [P for P in SemAcento if P not in Tentadas]
    if not Candidatos:
        return None

    Filtradas = _FiltrarPorFeedback(Candidatos, Jogador.Tentativas)
    TentativaNum = len(Jogador.Tentativas) + 1

    if Estado.Perfil == "falha":
        return random.choice(Filtradas[: min(800, len(Filtradas))])

    if Estado.TentativaVitoria is not None and TentativaNum >= Estado.TentativaVitoria:
        return ObterPalavraComAcento(PalavraSecreta) or PalavraSecreta

    Pontos = PontosBotPorIdJogador(Jogador.IdJogador) or 1200
    Skill = max(0.15, min(0.85, Pontos / 2600))
    Chance = 0.02 + Skill * 0.08
    if Estado.TentativaVitoria is not None and TentativaNum >= Estado.TentativaVitoria:
        Chance += 0.35
    if random.random() < Chance:
        return ObterPalavraComAcento(PalavraSecreta) or PalavraSecreta

    return random.choice(Filtradas[: min(800, len(Filtradas))])


def ProcessarBotsNasSalas(Gerenciador) -> list:
    Alteradas = []
    Agora = time.time()
    for Sala in list(Gerenciador.Salas.values()):
        if Sala.PartidaEncerrada or Sala.EstadoSala != "jogando":
            continue
        Bots = [
            J
            for J in Sala.Jogadores.values()
            if getattr(J, "EhBot", False) and not J.Espectador
        ]
        if not Bots:
            continue
        for Bot in Bots:
            if Bot.Finalizou:
                continue
            Estado = _GarantirEstado(Sala, Bot)
            if Agora < Estado.ProximoChuteEpoch:
                continue
            PalavraSecreta, _ = Gerenciador.ObterPalavraJogador(Sala, Bot)
            if not PalavraSecreta:
                continue
            Palavra = EscolherPalavraChute(Bot, PalavraSecreta, Estado)
            if not Palavra:
                continue
            Norm = NormalizarPalavra(Palavra.strip().lower())
            if not PalavraExisteNoDicionario(Norm):
                continue
            if Gerenciador.AplicarChuteJogador(Sala, Bot.IdJogador, Norm):
                Estado.ChuteNumero += 1
                Estado.ProximoChuteEpoch = Agora + INTERVALO_ENTRE_CHUTES_SEG
                Alteradas.append(Sala)
    return Alteradas
