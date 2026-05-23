import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.versao import ROTULO, VERSAO, InfoVersao, RotuloDeVersao


def test_versao_atual():
    assert VERSAO == "1.3.0"
    assert ROTULO == "v1.3"
    assert InfoVersao() == {"versao": "1.3.0", "rotulo": "v1.3"}


def test_rotulo_de_versao():
    assert RotuloDeVersao("1.2.0") == "v1.2"
    assert RotuloDeVersao("1.2.1") == "v1.2.1"
    assert RotuloDeVersao("1.1.0") == "v1.1"
    assert RotuloDeVersao("1.2.3") == "v1.2.3"
    assert RotuloDeVersao("2.0.0") == "v2.0"
    assert RotuloDeVersao("3") == "v3"
