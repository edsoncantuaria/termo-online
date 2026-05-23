import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from servidor.aplicacao import CriarAplicacao


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "chute.db")
    persistencia.InicializarBanco()
    return TestClient(CriarAplicacao())


def test_chute_palavra_inexistente_rejeitada_no_servidor(cliente):
    I = cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "dueto"},
    )
    Corpo = I.json()
    R = cliente.post(
        "/api/jogar/chute",
        json={
            "idPartida": Corpo["idPartida"],
            "tokenPartida": Corpo["tokenPartida"],
            "palavra": "xxxxx",
            "nomeJogador": "teste",
        },
    )
    assert R.status_code == 200
    assert R.json()["valido"] is False
    assert "dicionário" in R.json()["mensagem"].lower()


def test_chute_repetido_invalido(cliente):
    I = cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "dueto"},
    )
    assert I.status_code == 200
    Corpo = I.json()
    Id = Corpo["idPartida"]
    Token = Corpo["tokenPartida"]
    Payload = {
        "idPartida": Id,
        "tokenPartida": Token,
        "palavra": "terno",
        "nomeJogador": "teste",
    }
    C1 = cliente.post("/api/jogar/chute", json=Payload)
    assert C1.json()["valido"] is True
    C2 = cliente.post("/api/jogar/chute", json=Payload)
    assert C2.json()["valido"] is False
    assert "já tentou" in C2.json()["mensagem"].lower()


def test_dicionario_info(cliente):
    D = cliente.get("/api/dicionario/info")
    assert D.status_code == 200
    Corpo = D.json()
    assert Corpo["total"] > 1000
    assert len(Corpo["hash"]) == 16


def test_dicionario_palavras(cliente):
    D = cliente.get("/api/dicionario/palavras")
    assert D.status_code == 200
    Corpo = D.json()
    assert len(Corpo["palavras"]) > 1000
    assert "termo" in Corpo["palavras"]
    assert len(Corpo["hash"]) == 16


def test_iniciar_dueto_nao_vaza_secreto(cliente):
    I = cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "dueto"},
    )
    assert I.status_code == 200
    Tabs = I.json().get("tabuleiros") or []
    assert len(Tabs) >= 2
    for Tab in Tabs:
        assert "palavraSecreta" not in Tab
        assert "palavraComAcento" not in Tab


def test_chute_token_invalido(cliente):
    I = cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "dueto"},
    )
    Id = I.json()["idPartida"]
    R = cliente.post(
        "/api/jogar/chute",
        json={
            "idPartida": Id,
            "tokenPartida": "token-errado",
            "palavra": "terno",
            "nomeJogador": "teste",
        },
    )
    assert R.status_code == 403


def test_diaria_historico_exige_conta(cliente):
    assert cliente.get("/api/diaria/historico").status_code == 401


def test_diaria_grade_exige_conta(cliente):
    R = cliente.post(
        "/api/diaria/grade",
        json={
            "nick": "teste",
            "gradeTexto": "Termo Diária\n\n🟩⬛⬛⬛⬛",
            "venceu": True,
            "tentativasUsadas": 1,
            "pontos": 6,
        },
    )
    assert R.status_code == 401
