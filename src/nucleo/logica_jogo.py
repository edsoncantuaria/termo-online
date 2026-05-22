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


def _PalavraDeTentativa(Tentativa: dict) -> str:
    Palavra = Tentativa.get("palavra")
    if Palavra:
        return NormalizarPalavra(Palavra)
    Letras = Tentativa.get("letras") or []
    if Letras:
        return NormalizarPalavra("".join(str(L) for L in Letras))
    return ""


def PalavraJaFoiTentada(Tentativas: list[dict], PalavraNormalizada: str) -> bool:
    Alvo = NormalizarPalavra(PalavraNormalizada)
    if not Alvo:
        return False
    return any(_PalavraDeTentativa(T) == Alvo for T in Tentativas)


def _LetrasDeTentativaOuLinha(Tent: dict, Linha: dict | None = None) -> list[str]:
    Fonte = Linha if Linha is not None else Tent
    LetrasTent = list(NormalizarPalavra("".join(Fonte.get("letras") or [])))
    if len(LetrasTent) != TamanhoPalavra and Fonte.get("palavra"):
        LetrasTent = list(NormalizarPalavra(Fonte["palavra"]))
    while len(LetrasTent) < TamanhoPalavra:
        LetrasTent.append("")
    return LetrasTent[:TamanhoPalavra]


def _ValidarVerdesModoDificil(
    Letras: list[str],
    Estados: list,
    LetrasTent: list[str],
) -> tuple[bool, str | None]:
    for I, Estado in enumerate(Estados[:TamanhoPalavra]):
        if Estado == EstadoLetra.CORRETO.value and LetrasTent[I]:
            if Letras[I] != LetrasTent[I]:
                return (
                    False,
                    f"A letra '{LetrasTent[I].upper()}' deve ficar na posição {I + 1}.",
                )
    return True, None


def ValidarModoDificil(
    TentativasAnteriores: list[dict],
    PalavraNormalizada: str,
) -> tuple[bool, str | None]:
    """Modo difícil: letras verdes devem permanecer na mesma posição (solo e multi-tabuleiro)."""
    Letras = list(PalavraNormalizada)
    for Tent in TentativasAnteriores:
        Linhas = Tent.get("linhas")
        if Linhas:
            for Linha in Linhas:
                if Linha.get("venceu"):
                    continue
                Estados = Linha.get("estados") or []
                if not Estados:
                    continue
                LetrasTent = _LetrasDeTentativaOuLinha(Tent, Linha)
                Ok, Msg = _ValidarVerdesModoDificil(Letras, Estados, LetrasTent)
                if not Ok:
                    return Ok, Msg
            continue

        Estados = Tent.get("estados") or []
        if not Estados:
            continue
        LetrasTent = _LetrasDeTentativaOuLinha(Tent)
        Ok, Msg = _ValidarVerdesModoDificil(Letras, Estados, LetrasTent)
        if not Ok:
            return Ok, Msg
    return True, None


def ValidarPalavra(
    Palavra: str,
    TentativasAnteriores: list[dict] | None = None,
    ModoDificil: bool = False,
) -> tuple[bool, str | None]:
    PalavraNormalizada = NormalizarPalavra(Palavra)

    if len(PalavraNormalizada) != TamanhoPalavra:
        return False, "A palavra deve ter exatamente 5 letras."

    if not PalavraExisteNoDicionario(PalavraNormalizada):
        return False, "Palavra não encontrada no dicionário."

    if TentativasAnteriores and PalavraJaFoiTentada(TentativasAnteriores, PalavraNormalizada):
        return False, "Você já tentou essa palavra."

    if ModoDificil and TentativasAnteriores:
        Ok, Msg = ValidarModoDificil(TentativasAnteriores, PalavraNormalizada)
        if not Ok:
            return False, Msg

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


def SecretaSatisfazFeedback(
    PalavraSecreta: str,
    PalavraChute: str,
    Estados: list[EstadoLetra],
) -> bool:
    """A secreta deve reproduzir o mesmo feedback ao reavaliar o chute."""
    Gerado = AvaliarChute(PalavraSecreta, PalavraChute)
    return [E.value for E in Gerado] == [E.value for E in Estados]
