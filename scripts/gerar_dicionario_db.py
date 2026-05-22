#!/usr/bin/env python3
"""
Gera src/dicionario.txt a partir de dicionario/dicionario.db.

Requer: banco SQLite com tabela `words` (coluna `word`).
Uso: python scripts/gerar_dicionario_db.py [--db CAMINHO] [--saida CAMINHO]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from unidecode import unidecode

LETRA = re.compile(r"^[a-zàáâãéêíóôõúçüñ]+$", re.I)
VOGAIS = frozenset("aeiouáéíóúàâãêôõü")
CONSOANTES_SEGUIDAS = re.compile(r"[bcdfghjklmnpqrstvwxzç]{4,}")


def EhPalavraJogavel(Palavra: str) -> bool:
    if len(Palavra) != 5 or "-" in Palavra:
        return False
    if not LETRA.match(Palavra):
        return False

    Normalizada = unidecode(Palavra.lower())
    Vogais = sum(1 for Letra in Normalizada if Letra in VOGAIS)
    if Vogais < 2:
        return False

    if CONSOANTES_SEGUIDAS.search(Normalizada):
        return False

    return True


def EscolherFormaComAcento(Formas: list[str]) -> str:
    ComAcento = [F for F in Formas if F != unidecode(F)]
    if ComAcento:
        return sorted(ComAcento)[0]
    return sorted(Formas)[0]


def CarregarPalavrasDoBanco(CaminhoDb: Path) -> list[str]:
    Conexao = sqlite3.connect(CaminhoDb)
    try:
        Cursor = Conexao.cursor()
        Cursor.execute("SELECT word FROM words WHERE length(word) = 5")
        return [Linha[0].strip().lower() for Linha in Cursor.fetchall() if Linha[0]]
    finally:
        Conexao.close()


def Gerar(CaminhoDb: Path, CaminhoSaida: Path) -> int:
    Brutas = CarregarPalavrasDoBanco(CaminhoDb)
    print(f"Palavras de 5 letras no banco: {len(Brutas)}")

    PorChave: dict[str, list[str]] = defaultdict(list)
    for Palavra in Brutas:
        if not EhPalavraJogavel(Palavra):
            continue
        PorChave[unidecode(Palavra)].append(Palavra)

    Lista = sorted(
        (EscolherFormaComAcento(Formas) for Formas in PorChave.values()),
        key=lambda P: unidecode(P),
    )

    CaminhoSaida.parent.mkdir(parents=True, exist_ok=True)
    CaminhoSaida.write_text("\n".join(Lista) + "\n", encoding="utf-8")
    print(f"Palavras gravadas em {CaminhoSaida}: {len(Lista)}")
    return len(Lista)


def main() -> None:
    RaizProjeto = Path(__file__).resolve().parent.parent
    PadraoDb = RaizProjeto / "dicionario" / "dicionario.db"

    Parser = argparse.ArgumentParser(
        description="Gera dicionario.txt (5 letras) a partir de dicionario.db."
    )
    Parser.add_argument("--db", type=Path, default=PadraoDb)
    Parser.add_argument(
        "--saida",
        type=Path,
        default=RaizProjeto / "src" / "dicionario.txt",
    )
    Args = Parser.parse_args()

    if not Args.db.is_file():
        raise SystemExit(f"Banco não encontrado: {Args.db}")

    Gerar(Args.db, Args.saida)


if __name__ == "__main__":
    main()
