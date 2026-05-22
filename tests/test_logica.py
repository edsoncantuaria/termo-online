import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.logica_jogo import (
    AvaliarChute,
    PalavraFoiAcertada,
    PalavraJaFoiTentada,
    ValidarPalavra,
)


def test_avaliar_chute_verde_e_dourado():
    Estados = AvaliarChute("termo", "terno")
    Valores = [E.value for E in Estados]
    assert Valores.count("correto") >= 1
    assert "presente" in Valores or "ausente" in Valores


def test_palavra_acertada():
    assert PalavraFoiAcertada("termo", "termo") is True
    assert PalavraFoiAcertada("termo", "terno") is False


def test_validar_tamanho():
    Valido, _ = ValidarPalavra("abc")
    assert Valido is False
    Valido, Palavra = ValidarPalavra("termo")
    assert Valido is True
    assert Palavra == "termo"


def test_palavra_repetida():
    Anteriores = [{"palavra": "termo", "letras": list("TERMO"), "estados": []}]
    assert PalavraJaFoiTentada(Anteriores, "termo") is True
    assert PalavraJaFoiTentada(Anteriores, "terno") is False
    Valido, Msg = ValidarPalavra("termo", Anteriores)
    assert Valido is False
    assert "já tentou" in (Msg or "").lower()
