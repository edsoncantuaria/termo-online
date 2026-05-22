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


def test_chute_repetido_invalido(cliente):
    I = cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "pratica"},
    )
    assert I.status_code == 200
    Id = I.json()["idPartida"]
    C1 = cliente.post(
        "/api/jogar/chute",
        json={"idPartida": Id, "palavra": "termo", "nomeJogador": "teste"},
    )
    assert C1.json()["valido"] is True
    C2 = cliente.post(
        "/api/jogar/chute",
        json={"idPartida": Id, "palavra": "termo", "nomeJogador": "teste"},
    )
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
