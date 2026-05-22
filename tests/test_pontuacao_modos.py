import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.modos_solo import ModoDueto, ModoQuarteto, TentativasDueto, TentativasQuarteto
from nucleo.pontuacao import CalcularPontuacao


def test_dueto_sexta_tentativa_reconhece_7_maximo():
    """Com teto 6, a 6ª tentativa no dueto não ganhava bônus de sobra."""
    Pratica6 = CalcularPontuacao(True, 6, "pratica")
    Dueto6 = CalcularPontuacao(True, 6, ModoDueto)
    assert Dueto6 > Pratica6


def test_quarteto_setima_tentativa_reconhece_9_maximo():
    Pratica6 = CalcularPontuacao(True, 6, "pratica")
    Quarteto7 = CalcularPontuacao(True, 7, ModoQuarteto)
    assert Quarteto7 > Pratica6


def test_dueto_setima_tentativa_ultima_ainda_pontua():
    assert CalcularPontuacao(True, TentativasDueto, ModoDueto) >= 100
