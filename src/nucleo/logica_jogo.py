import random
from enum import Enum

from .dicionario import NormalizarPalavra, ObterDicionario, PalavraExisteNoDicionario


class EstadoLetra(str, Enum):
    CORRETO = "correto"
    PRESENTE = "presente"
    AUSENTE = "ausente"


MaximoTentativas = 6
TamanhoPalavra = 5
ModoDiaria = "diaria"
ModoPratica = "pratica"
ModoArena = "arena"


def EscolherPalavraAleatoria() -> tuple[str, str]:
    PalavrasComAcento, PalavrasSemAcento, _ = ObterDicionario()
    Indice = random.randrange(len(PalavrasSemAcento))
    return PalavrasSemAcento[Indice], PalavrasComAcento[Indice]


def ValidarPalavra(Palavra: str) -> tuple[bool, str | None]:
    PalavraNormalizada = NormalizarPalavra(Palavra)

    if len(PalavraNormalizada) != TamanhoPalavra:
        return False, "A palavra deve ter exatamente 5 letras."

    if not PalavraExisteNoDicionario(PalavraNormalizada):
        return False, "Palavra não encontrada no dicionário."

    return True, PalavraNormalizada


def AvaliarChute(PalavraSecreta: str, PalavraChute: str) -> list[EstadoLetra]:
    LetrasSecretas = list(PalavraSecreta)
    LetrasChute = list(PalavraChute)
    Resultado = [EstadoLetra.AUSENTE] * TamanhoPalavra

    for Indice in range(TamanhoPalavra):
        if LetrasChute[Indice] == LetrasSecretas[Indice]:
            Resultado[Indice] = EstadoLetra.CORRETO
            LetrasSecretas[Indice] = None
            LetrasChute[Indice] = None

    for Indice in range(TamanhoPalavra):
        if LetrasChute[Indice] is None:
            continue
        if LetrasChute[Indice] in LetrasSecretas:
            Resultado[Indice] = EstadoLetra.PRESENTE
            Posicao = LetrasSecretas.index(LetrasChute[Indice])
            LetrasSecretas[Posicao] = None

    return Resultado


def PalavraFoiAcertada(PalavraSecreta: str, PalavraChute: str) -> bool:
    return PalavraSecreta == NormalizarPalavra(PalavraChute)
