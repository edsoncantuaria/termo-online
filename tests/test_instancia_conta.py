"""Uma instância ativa por conta (dispositivo/aba com login novo)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.contas import LoginConta, RegistrarConta
from servidor.aplicacao import CriarAplicacao


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "inst.db")
    persistencia.InicializarBanco()
    return TestClient(CriarAplicacao())


def test_login_emite_instancia_e_rejeita_outra(cliente):
    _Perfil, Token, Inst1 = RegistrarConta("inst_a", "inst_a@test.com", "senha123")
    R_ok = cliente.get(
        "/api/auth/eu",
        headers={
            "Authorization": f"Bearer {Token}",
            "X-Termo-Instancia": Inst1,
        },
    )
    assert R_ok.status_code == 200

    _Perfil2, Token2, Inst2 = LoginConta("inst_a@test.com", "senha123")
    assert Inst2 != Inst1

    R_conflict = cliente.get(
        "/api/auth/eu",
        headers={
            "Authorization": f"Bearer {Token}",
            "X-Termo-Instancia": Inst1,
        },
    )
    assert R_conflict.status_code == 409

    R_novo = cliente.get(
        "/api/auth/eu",
        headers={
            "Authorization": f"Bearer {Token2}",
            "X-Termo-Instancia": Inst2,
        },
    )
    assert R_novo.status_code == 200
