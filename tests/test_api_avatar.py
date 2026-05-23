import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.contas import RegistrarConta
from servidor.aplicacao import CriarAplicacao


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "api_av.db")
    persistencia.InicializarBanco()
    return TestClient(CriarAplicacao())


def test_patch_avatar(cliente):
    Perfil, Token, _ = RegistrarConta("api_av", "apiav@test.com", "senha123")
    R = cliente.patch(
        "/api/auth/avatar",
        json={"avatarId": "abelha"},
        headers={"Authorization": f"Bearer {Token}"},
    )
    assert R.status_code == 200
    assert R.json()["conta"]["avatarId"] == "abelha"


def test_listar_avatares(cliente):
    R = cliente.get("/api/auth/avatares")
    assert R.status_code == 200
    assert "folha" in R.json()["avatares"]
