"""Simulação de chutes para oponentes bot em duelos ranqueados."""

from __future__ import annotations

import random
import time

from .bots_ranqueados import PontosBotPorIdJogador
from .dicionario import ObterDicionario, ObterPalavraComAcento, PalavraExisteNoDicionario
from .logica_jogo import AvaliarChute, MaximoTentativas, PalavraFoiAcertada

_ULTIMO_CHUTE: dict[str, float] = {}
_INTERVALO_MIN = 2.8
_INTERVALO_MAX = 6.5


def _IntervaloChuteBot(Jogador) -> float:
    from .bots_ranqueados import PontosBotPorIdJogador

    Pontos = PontosBotPorIdJogador(Jogador.IdJogador) or 1200
    Fator = max(0.35, min(1.0, Pontos / 2200))
    return _INTERVALO_MIN + (1.0 - Fator) * (_INTERVALO_MAX - _INTERVALO_MIN)


def _FiltrarPorFeedback(Candidatos: list[str], Tentativas: list[dict]) -> list[str]:
    if not Tentativas:
        return Candidatos
    Ultima = Tentativas[-1]
    Letras = Ultima.get("letras") or list(Ultima.get("palavra", ""))
    Estados = Ultima.get("estados") or []
    if len(Letras) != len(Estados):
        return Candidatos

    Verdes: dict[int, str] = {}
    Amarelas: list[str] = []
    Cinzas: set[str] = set()

    for I, (L, E) in enumerate(zip(Letras, Estados)):
        Ln = str(L).lower()
        if E == "correta":
            Verdes[I] = Ln
        elif E == "presente":
            Amarelas.append(Ln)
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
                if all(
                    Estados[J] != "correta" or str(Letras[J]).lower() != Letra
                    for J in range(len(Letras))
                    if str(Letras[J]).lower() == Letra
                ):
                    if Palavra.count(Letra) > sum(
                        1 for J in range(5) if Palavra[J] == Letra and J in Verdes
                    ):
                        Ok = False
                        break
        if Ok:
            Filtradas.append(Palavra)
    return Filtradas or Candidatos


def EscolherPalavraChute(Jogador, PalavraSecreta: str) -> str | None:
    _, SemAcento, _ = ObterDicionario()
    Tentadas = {
        t.get("palavra", "").lower()
        for t in Jogador.Tentativas
        if t.get("palavra")
    }
    Candidatos = [P for P in SemAcento if P not in Tentadas]
    if not Candidatos:
        return None

    Pontos = PontosBotPorIdJogador(Jogador.IdJogador) or 1200
    Skill = max(0.2, min(0.95, Pontos / 2600))
    Filtradas = _FiltrarPorFeedback(Candidatos, Jogador.Tentativas)

    TentativaNum = len(Jogador.Tentativas) + 1
    ChanceAcerto = 0.03 + Skill * 0.24
    if TentativaNum >= 4:
        ChanceAcerto += Skill * 0.14
    if TentativaNum >= 5:
        ChanceAcerto += 0.1 + Skill * 0.05

    if random.random() < ChanceAcerto:
        return ObterPalavraComAcento(PalavraSecreta) or PalavraSecreta

    return random.choice(Filtradas[: min(800, len(Filtradas))])


def ProcessarBotsNasSalas(Gerenciador) -> list:
    """Retorna salas que mudaram e precisam de broadcast."""
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
            if Agora - _ULTIMO_CHUTE.get(Bot.IdJogador, 0) < _IntervaloChuteBot(Bot):
                continue
            PalavraSecreta, _ = Gerenciador.ObterPalavraJogador(Sala, Bot)
            if not PalavraSecreta:
                continue
            Palavra = EscolherPalavraChute(Bot, PalavraSecreta)
            if not Palavra:
                continue
            Norm = Palavra.strip().lower()
            from .dicionario import NormalizarPalavra

            Norm = NormalizarPalavra(Norm)
            if not PalavraExisteNoDicionario(Norm):
                continue
            if Gerenciador.AplicarChuteJogador(Sala, Bot.IdJogador, Norm):
                _ULTIMO_CHUTE[Bot.IdJogador] = Agora
                Alteradas.append(Sala)
    return Alteradas
