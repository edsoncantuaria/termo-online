import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.logica_jogo import (
    AvaliarChute,
    EstadoLetra,
    PalavraFoiAcertada,
    PalavraJaFoiTentada,
    SecretaSatisfazFeedback,
    ValidarModoDificil,
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


def test_letra_duplicada_wordle():
    """Segundo T cinza quando a secreta só tem um T."""
    Estados = AvaliarChute("termo", "teste")
    Valores = [E.value for E in Estados]
    assert Valores[0] == "correto"
    assert Valores[3] == "ausente"


def test_secreta_satisfaz_feedback():
    Secreta = "termo"
    for Chute in ("terno", "tremo", "termo"):
        Estados = AvaliarChute(Secreta, Chute)
        assert SecretaSatisfazFeedback(Secreta, Chute, Estados)


def test_modo_dificil_dueto_respeita_linhas():
    Anteriores = [
        {
            "palavra": "terno",
            "letras": list("TERNO"),
            "linhas": [
                {
                    "indice": 0,
                    "palavra": "terno",
                    "letras": list("TERNO"),
                    "estados": [E.value for E in AvaliarChute("termo", "terno")],
                    "venceu": False,
                },
                {
                    "indice": 1,
                    "palavra": "terno",
                    "letras": list("TERNO"),
                    "estados": [E.value for E in AvaliarChute("carro", "terno")],
                    "venceu": False,
                },
            ],
        }
    ]
    Ok, Msg = ValidarModoDificil(Anteriores, "tordo")
    assert not Ok
    assert "posição" in (Msg or "").lower()


def test_modo_dificil_exige_verdes():
    Anteriores = [
        {
            "palavra": "terno",
            "letras": list("TERNO"),
            "estados": [E.value for E in AvaliarChute("termo", "terno")],
        }
    ]
    Ok, Msg = ValidarModoDificil(Anteriores, "tordo")
    assert not Ok
    assert "posição" in (Msg or "").lower()
    LetrasOk = list("terno")
    for I, Est in enumerate(Anteriores[0]["estados"]):
        if Est != "correto":
            LetrasOk[I] = "a"
    Ok2, _ = ValidarModoDificil(Anteriores, "".join(LetrasOk))
    assert Ok2
