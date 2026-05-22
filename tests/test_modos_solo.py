import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.modos_solo import (
    CriarTabuleiros,
    GerarSeedDesafio,
    MaximoTentativasModo,
    ModoDueto,
    ModoQuarteto,
    AvaliarChuteTabuleiros,
)


def test_dueto_tem_duas_palavras():
    Tabs = CriarTabuleiros(ModoDueto)
    assert len(Tabs) == 2
    assert MaximoTentativasModo(ModoDueto) == 7


def test_quarteto():
    Tabs = CriarTabuleiros(ModoQuarteto)
    assert len(Tabs) == 4
    assert MaximoTentativasModo(ModoQuarteto) == 9


def test_desafio_mesmo_codigo():
    A = CriarTabuleiros("desafio", CodigoDesafio="ABC123")
    B = CriarTabuleiros("desafio", CodigoDesafio="ABC123")
    assert A[0]["palavraSecreta"] == B[0]["palavraSecreta"]


def test_chute_multi():
    Tabs = CriarTabuleiros(ModoDueto, CodigoDesafio="TEST01")
    Palavra = Tabs[0]["palavraSecreta"]
    R = AvaliarChuteTabuleiros(Tabs, Palavra)
    assert R["todasVencidas"] or any(L.get("venceu") for L in R["linhas"])
