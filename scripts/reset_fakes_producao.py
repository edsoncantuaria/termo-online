#!/usr/bin/env python3
"""Reset das contas fake (bots + validação da população passiva) para produção.

Nenhum fake deve ter RP de Prata ou acima (máx. bronze: RP < 1600).

Uso (na raiz do projeto, com venv ativo):
  make backup-db          # recomendado antes
  make reset-fakes

Ou:
  .venv/bin/python3 scripts/reset_fakes_producao.py [--banco data/termo.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from nucleo import persistencia  # noqa: E402
from nucleo.bots_ranqueados import (  # noqa: E402
    BOTS,
    RP_MAXIMO_BOTS,
    ResetarBotsRanqueadosParaPadrao,
)
from nucleo.ranqueada import EloDePontos  # noqa: E402
from nucleo.ranking_ranqueado import _POPULACAO_PASSIVA  # noqa: E402

ELOS_PROIBIDOS_FAKE = frozenset({"prata", "ouro", "platina", "diamante", "estrela"})


def ValidarPopulacaoPassiva() -> tuple[int, int]:
    MaxRp = 0
    Violacoes = 0
    for E in _POPULACAO_PASSIVA:
        P = int(E["pontos"])
        MaxRp = max(MaxRp, P)
        if P > RP_MAXIMO_BOTS or EloDePontos(P) in ELOS_PROIBIDOS_FAKE:
            Violacoes += 1
    return MaxRp, Violacoes


def ValidarBotsIniciais() -> int:
    Violacoes = 0
    for B in BOTS:
        if B.Pontos > RP_MAXIMO_BOTS or EloDePontos(B.Pontos) in ELOS_PROIBIDOS_FAKE:
            Violacoes += 1
    return Violacoes


def main() -> int:
    Parser = argparse.ArgumentParser(description=__doc__)
    Parser.add_argument(
        "--banco",
        type=Path,
        default=RAIZ / "data" / "termo.db",
        help="Caminho do SQLite (padrão: data/termo.db)",
    )
    Args = Parser.parse_args()

    if not Args.banco.is_file():
        print(f"Erro: banco não encontrado: {Args.banco}", file=sys.stderr)
        return 1

    persistencia.CaminhoBanco = Args.banco
    persistencia.InicializarBanco()

    Removidos = ResetarBotsRanqueadosParaPadrao()
    MaxPass, ViolPass = ValidarPopulacaoPassiva()
    ViolBots = ValidarBotsIniciais()

    print(f"Banco: {Args.banco}")
    print(f"Registros removidos em bots_ranqueados_estado: {Removidos}")
    print(f"Bots reiniciados: {len(BOTS)} (RP máx. permitido: {RP_MAXIMO_BOTS})")
    print(f"População passiva: {len(_POPULACAO_PASSIVA)} entradas, RP máx. {MaxPass}")

    if ViolPass or ViolBots:
        print(
            f"ERRO: {ViolPass} violação(ões) na população passiva, "
            f"{ViolBots} nos bots iniciais — Prata+ não permitido.",
            file=sys.stderr,
        )
        return 2

    print("OK — fakes limitados a Papelão/Madeira/Ferro/Bronze.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
