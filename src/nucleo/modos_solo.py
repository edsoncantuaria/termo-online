"""Modos solo: dueto, quarteto, desafio e dificuldade."""

import random

from .dicionario import ObterDicionario, ObterPalavraComAcento
from .logica_jogo import (
    AvaliarChute,
    EscolherPalavraAleatoria,
    MaximoTentativas,
    PalavraFoiAcertada,
)

ModoPratica = "pratica"
ModoDiaria = "diaria"
ModoDueto = "dueto"
ModoQuarteto = "quarteto"
ModoDesafio = "desafio"
DificuldadeNormal = "normal"
DificuldadeDificil = "dificil"

TentativasDueto = 7
TentativasQuarteto = 9


def MaximoTentativasModo(Modo: str) -> int:
    if Modo == ModoDueto:
        return TentativasDueto
    if Modo == ModoQuarteto:
        return TentativasQuarteto
    return MaximoTentativas


def QuantidadePalavrasModo(Modo: str) -> int:
    if Modo == ModoDueto:
        return 2
    if Modo == ModoQuarteto:
        return 4
    return 1


def EscolherPalavraPorSeed(Seed: int, Indice: int = 0, Dificuldade: str = DificuldadeNormal) -> tuple[str, str]:
    Rng = random.Random(Seed + Indice * 7919)
    _, PalavrasSem, _ = ObterDicionario()
    if not PalavrasSem:
        return EscolherPalavraAleatoria()
    if Dificuldade == DificuldadeDificil:
        Inicio = len(PalavrasSem) // 2
        IndiceSort = Inicio + Rng.randrange(len(PalavrasSem) - Inicio)
    else:
        IndiceSort = Rng.randrange(len(PalavrasSem))
    Secreta = PalavrasSem[IndiceSort]
    return Secreta, ObterPalavraComAcento(Secreta) or Secreta


def GerarSeedDesafio(Codigo: str) -> int:
    Codigo = Codigo.strip().upper()[:8]
    return sum((I + 1) * ord(C) for I, C in enumerate(Codigo)) % (2**31)


def CriarTabuleiros(
    Modo: str,
    Dificuldade: str = DificuldadeNormal,
    CodigoDesafio: str | None = None,
) -> list[dict]:
    Qtd = QuantidadePalavrasModo(Modo)
    if Qtd == 1:
        if CodigoDesafio:
            Secreta, ComAcento = EscolherPalavraPorSeed(
                GerarSeedDesafio(CodigoDesafio), 0, Dificuldade
            )
        elif Dificuldade == DificuldadeDificil:
            Secreta, ComAcento = EscolherPalavraPorSeed(
                random.randint(0, 2**30), 0, DificuldadeDificil
            )
        else:
            Secreta, ComAcento = EscolherPalavraAleatoria()
        return [
            {
                "indice": 0,
                "palavraSecreta": Secreta,
                "palavraComAcento": ComAcento,
                "venceu": False,
                "tentativas": [],
            }
        ]

    Seed = GerarSeedDesafio(CodigoDesafio) if CodigoDesafio else random.randint(0, 2**30)
    Tabuleiros = []
    for I in range(Qtd):
        Secreta, ComAcento = EscolherPalavraPorSeed(Seed, I, Dificuldade)
        Tabuleiros.append(
            {
                "indice": I,
                "palavraSecreta": Secreta,
                "palavraComAcento": ComAcento,
                "venceu": False,
                "tentativas": [],
            }
        )
    return Tabuleiros


def AvaliarChuteTabuleiros(Tabuleiros: list[dict], PalavraChute: str) -> dict:
    Linhas = []
    for Tab in Tabuleiros:
        if Tab["venceu"]:
            Linhas.append({"indice": Tab["indice"], "venceu": True, "estados": [], "letras": []})
            continue
        Estados = [E.value for E in AvaliarChute(Tab["palavraSecreta"], PalavraChute)]
        Exib = ObterPalavraComAcento(PalavraChute) or PalavraChute
        Linha = {
            "indice": Tab["indice"],
            "palavra": Exib,
            "letras": list(Exib.upper()),
            "estados": Estados,
            "venceu": False,
        }
        if PalavraFoiAcertada(Tab["palavraSecreta"], PalavraChute):
            Tab["venceu"] = True
            Linha["venceu"] = True
        Tab["tentativas"].append(Linha)
        Linhas.append(Linha)

    return {"linhas": Linhas, "todasVencidas": all(T["venceu"] for T in Tabuleiros)}


def ContarTentativasGlobais(Tabuleiros: list[dict]) -> int:
    if not Tabuleiros:
        return 0
    return max(len(T.get("tentativas", [])) for T in Tabuleiros)


def TabuleirosParaCliente(
    Tabuleiros: list[dict] | None,
    RevelarSegredos: bool = False,
) -> list[dict] | None:
    """Remove palavras secretas da resposta HTTP enquanto a partida não encerrou."""
    if not Tabuleiros:
        return None
    Saida = []
    for Tab in Tabuleiros:
        Item = {
            "indice": Tab["indice"],
            "venceu": Tab.get("venceu", False),
            "tentativas": Tab.get("tentativas", []),
        }
        if RevelarSegredos:
            Item["palavraComAcento"] = Tab.get("palavraComAcento")
        Saida.append(Item)
    return Saida
