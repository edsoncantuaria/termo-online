import hashlib
from pathlib import Path
from unidecode import unidecode

CaminhoDicionario = Path(__file__).resolve().parent.parent / "dicionario.txt"

PalavrasComAcento: list[str] = []
PalavrasSemAcento: list[str] = []
IndicePorPalavra: dict[str, int] = {}


def CarregarDicionario() -> None:
    global PalavrasComAcento, PalavrasSemAcento, IndicePorPalavra

    with open(CaminhoDicionario, encoding="utf-8") as Arquivo:
        PalavrasComAcento = [
            Linha.strip().lower()
            for Linha in Arquivo
            if len(Linha.strip()) == 5
        ]

    PalavrasSemAcento = [unidecode(Palavra) for Palavra in PalavrasComAcento]
    IndicePorPalavra = {Palavra: Indice for Indice, Palavra in enumerate(PalavrasSemAcento)}


def ObterDicionario() -> tuple[list[str], list[str], dict[str, int]]:
    if not PalavrasSemAcento:
        CarregarDicionario()
    return PalavrasComAcento, PalavrasSemAcento, IndicePorPalavra


def NormalizarPalavra(Palavra: str) -> str:
    return unidecode(Palavra.strip().lower())


def PalavraExisteNoDicionario(PalavraNormalizada: str) -> bool:
    _, _, Indice = ObterDicionario()
    return PalavraNormalizada in Indice


def ObterPalavraComAcento(PalavraNormalizada: str) -> str | None:
    _, _, Indice = ObterDicionario()
    IndicePalavra = Indice.get(PalavraNormalizada)
    if IndicePalavra is None:
        return None
    PalavrasComAcentoLista, _, _ = ObterDicionario()
    return PalavrasComAcentoLista[IndicePalavra]


def ObterHashDicionario() -> str:
    """Hash estável para cache do cliente validar palavras offline."""
    _, PalavrasSem, _ = ObterDicionario()
    Conteudo = "\n".join(PalavrasSem).encode("utf-8")
    return hashlib.sha256(Conteudo).hexdigest()[:16]


def PalavraExisteNoConjuntoLocal(PalavraNormalizada: str, Conjunto: set[str] | None) -> bool:
    if Conjunto is not None:
        return PalavraNormalizada in Conjunto
    return PalavraExisteNoDicionario(PalavraNormalizada)
