#!/usr/bin/env python3
"""
Gera src/dicionario.txt a partir do Hunspell Português (Brasil).

Fonte: https://github.com/titoBouzout/Dictionaries
Arquivos: Portuguese (Brazilian).dic + .aff

Requer: pip install spylls unidecode
Uso: python scripts/gerar_dicionario.py [--dic CAMINHO] [--aff CAMINHO] [--saida CAMINHO]
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

from unidecode import unidecode

URL_BASE = (
    "https://raw.githubusercontent.com/titoBouzout/Dictionaries/refs/heads/master/"
)
ARQUIVO_DIC = "Portuguese%20(Brazilian).dic"
ARQUIVO_AFF = "Portuguese%20(Brazilian).aff"

LETRA = re.compile(r"^[a-zàáâãéêíóôõúçüñ]+$", re.I)
VOGAIS = frozenset("aeiouáéíóúàâãêôõü")
CONSOANTES_SEGUIDAS = re.compile(r"[bcdfghjklmnpqrstvwxzç]{4,}")


class IndiceDic:
    """Metadados do .dic para filtrar nomes próprios e siglas."""

    __slots__ = ("PropriosApenas", "Maiusculas")

    def __init__(self) -> None:
        self.PropriosApenas: set[str] = set()
        self.Maiusculas: set[str] = set()


def MontarIndiceDic(LinhasDic: list[str]) -> IndiceDic:
    Indice = IndiceDic()
    PorPalavra: dict[str, list[bool]] = {}

    for Linha in LinhasDic:
        Original = Linha.split("\t")[0].split("/")[0]
        Lexema = Original.lower()
        if len(Lexema) != 5 or "-" in Lexema:
            continue
        Chave = unidecode(Lexema)
        Proprio = bool(Original and Original[0].isupper() and not Original.isupper())
        PorPalavra.setdefault(Chave, []).append(Proprio)
        if Original.isupper() and Original.isalpha():
            Indice.Maiusculas.add(Chave)

    for Chave, Marcadores in PorPalavra.items():
        if all(Marcadores):
            Indice.PropriosApenas.add(Chave)

    return Indice


def EhPalavraJogavel(Palavra: str, Indice: IndiceDic) -> bool:
    if not LETRA.match(Palavra):
        return False

    Normalizada = unidecode(Palavra.lower())
    if Normalizada in Indice.PropriosApenas or Normalizada in Indice.Maiusculas:
        return False

    Vogais = sum(1 for Letra in Normalizada if Letra in VOGAIS)
    if Vogais < 2:
        return False

    if CONSOANTES_SEGUIDAS.search(Normalizada):
        return False

    return True


SUF_REMOVER = (
    "ção",
    "ções",
    "dade",
    "mente",
    "inho",
    "inha",
    "eiro",
    "eira",
    "ável",
    "ível",
    "ado",
    "ada",
    "oso",
    "osa",
    "ista",
    "ismo",
    "ante",
    "ente",
    "ação",
    "ador",
    "ico",
    "ica",
    "ivo",
    "iva",
    "eza",
    "ório",
    "ória",
)


def BaixarSeNecessario(Destino: Path, NomeRemoto: str) -> Path:
    if Destino.exists():
        return Destino
    Destino.parent.mkdir(parents=True, exist_ok=True)
    Url = URL_BASE + NomeRemoto
    print(f"Baixando {Url} ...")
    urllib.request.urlretrieve(Url, Destino)
    return Destino


def ExtrairLexema(Linha: str) -> str:
    Parte = Linha.split("\t")[0].strip()
    return Parte.split("/")[0].lower()


def EhNomeProprio(Linha: str) -> bool:
    Original = Linha.split("\t")[0].split("/")[0]
    return bool(Original and Original[0].isupper() and not Original.isupper())


def MontarCandidatos(LinhasDic: list[str]) -> set[str]:
    Candidatos: set[str] = set()

    for Linha in LinhasDic:
        if EhNomeProprio(Linha):
            continue
        Lexema = ExtrairLexema(Linha)
        if len(Lexema) == 5 and "-" not in Lexema and LETRA.match(Lexema):
            Candidatos.add(Lexema)

    for Linha in LinhasDic:
        if EhNomeProprio(Linha):
            continue
        Lexema = ExtrairLexema(Linha)
        if "-" in Lexema or not LETRA.match(Lexema):
            continue
        for SufixoVerbal in ("ar", "er", "ir", "or"):
            if not Lexema.endswith(SufixoVerbal):
                continue
            Raiz = Lexema[:-2]
            for Terminacao in (
                "a",
                "e",
                "o",
                "as",
                "es",
                "am",
                "em",
                "ou",
                "ei",
                "ia",
                "iu",
                "ão",
            ):
                Palavra = Raiz + Terminacao
                if len(Palavra) == 5:
                    Candidatos.add(Palavra)
            if len(Raiz) == 3:
                for Terminacao in ("ava", "ado", "ada", "ido", "ida"):
                    Palavra = Raiz + Terminacao
                    if len(Palavra) == 5:
                        Candidatos.add(Palavra)

    for Linha in LinhasDic:
        if EhNomeProprio(Linha):
            continue
        Lexema = ExtrairLexema(Linha)
        if len(Lexema) <= 5 or "-" in Lexema:
            continue
        for Sufixo in SUF_REMOVER:
            if Lexema.endswith(Sufixo) and len(Lexema) - len(Sufixo) == 5:
                Candidatos.add(Lexema[: -len(Sufixo)])
        for Indice in range(len(Lexema) - 4):
            Palavra = Lexema[Indice : Indice + 5]
            if LETRA.match(Palavra):
                Candidatos.add(Palavra)

    return Candidatos


def ValidarComHunspell(Candidatos: set[str], CaminhoBase: Path) -> dict[str, str]:
    from spylls.hunspell import Dictionary

    DicionarioHunspell = Dictionary.from_files(str(CaminhoBase))
    Validas: dict[str, str] = {}
    for Palavra in Candidatos:
        if DicionarioHunspell.lookup(Palavra):
            Chave = unidecode(Palavra)
            if Chave not in Validas:
                Validas[Chave] = Palavra
    return Validas


def Gerar(
    CaminhoDic: Path,
    CaminhoAff: Path,
    CaminhoSaida: Path,
    *,
    Baixar: bool = False,
) -> int:
    RaizCache = Path(__file__).resolve().parent / ".cache_hunspell"
    if Baixar:
        CaminhoDic = BaixarSeNecessario(RaizCache / "pt_BR.dic", ARQUIVO_DIC)
        CaminhoAff = BaixarSeNecessario(RaizCache / "pt_BR.aff", ARQUIVO_AFF)

    Base = CaminhoDic.with_suffix("")
    if Base.name != CaminhoAff.with_suffix("").name:
        Copia = RaizCache / "pt_BR"
        Copia.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy(CaminhoDic, Copia / "pt_BR.dic")
        shutil.copy(CaminhoAff, Copia / "pt_BR.aff")
        Base = Copia / "pt_BR"

    LinhasDic = CaminhoDic.read_text(encoding="utf-8", errors="replace").splitlines()[1:]
    Indice = MontarIndiceDic(LinhasDic)
    Candidatos = MontarCandidatos(LinhasDic)
    print(f"Candidatos gerados: {len(Candidatos)}")

    Validas = ValidarComHunspell(Candidatos, Base)

    for Linha in LinhasDic:
        if EhNomeProprio(Linha):
            continue
        Lexema = ExtrairLexema(Linha)
        if len(Lexema) == 5:
            Chave = unidecode(Lexema)
            if Chave in Validas:
                Validas[Chave] = Lexema

    AntesFiltro = len(Validas)
    Validas = {
        Chave: Palavra
        for Chave, Palavra in Validas.items()
        if EhPalavraJogavel(Palavra, Indice)
    }
    print(f"Removidas (próprios/siglas/abrev.): {AntesFiltro - len(Validas)}")

    Lista = sorted(Validas.values(), key=lambda P: unidecode(P))
    CaminhoSaida.parent.mkdir(parents=True, exist_ok=True)
    CaminhoSaida.write_text("\n".join(Lista) + "\n", encoding="utf-8")
    print(f"Palavras gravadas em {CaminhoSaida}: {len(Lista)}")
    return len(Lista)


def main() -> None:
    RaizProjeto = Path(__file__).resolve().parent.parent
    PadraoCache = Path(__file__).resolve().parent / ".cache_hunspell"

    Parser = argparse.ArgumentParser(description="Gera dicionario.txt (5 letras, PT-BR).")
    Parser.add_argument("--dic", type=Path, default=PadraoCache / "pt_BR.dic")
    Parser.add_argument("--aff", type=Path, default=PadraoCache / "pt_BR.aff")
    Parser.add_argument("--saida", type=Path, default=RaizProjeto / "src" / "dicionario.txt")
    Parser.add_argument(
        "--baixar",
        action="store_true",
        help="Baixa .dic/.aff do GitHub se ainda não existirem",
    )
    Args = Parser.parse_args()

    if Args.baixar or not Args.dic.exists():
        Args.dic = BaixarSeNecessario(Args.dic, ARQUIVO_DIC)
        Args.aff = BaixarSeNecessario(Args.aff, ARQUIVO_AFF)

    Gerar(Args.dic, Args.aff, Args.saida, Baixar=False)


if __name__ == "__main__":
    main()
