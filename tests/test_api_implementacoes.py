"""Testes HTTP das implementações recentes (API)."""

import re
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from servidor.aplicacao import CriarAplicacao


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "api_impl.db")
    monkeypatch.delenv("TERM0_REDIS_URL", raising=False)
    persistencia.InicializarBanco()
    from servidor.estado_global import GerenciadorVersus

    GerenciadorVersus.Salas.clear()
    return TestClient(CriarAplicacao())


@pytest.mark.parametrize("modo", ["pratica", "dueto", "quarteto", "desafio"])
def test_api_iniciar_solo_retorna_uuid(cliente, modo):
    Corpo = {"nomeJogador": "Tester", "modo": modo}
    if modo == "desafio":
        Corpo["codigoDesafio"] = "ABC123"
    R = cliente.post("/api/jogar/iniciar", json=Corpo)
    assert R.status_code == 200
    D = R.json()
    assert D["idPartida"]
    uuid.UUID(D["idPartida"])
    assert D["tokenPartida"]
    assert D["modo"] == modo


def test_api_desafio_criar_sala_multijogador(cliente):
    R = cliente.post("/api/desafio/criar")
    assert R.status_code == 200
    D = R.json()
    assert len(D["codigoSala"]) == 6
    assert D["codigoDesafio"] == D["codigoSala"]
    assert D["link"] == f"/?sala={D['codigoSala']}"
    assert D["idPartida"]
    uuid.UUID(D["idPartida"])
    assert D["tokenSessao"]
    cfg = D.get("configuracao") or {}
    assert cfg.get("maximoJogadores") == 4
    assert cfg.get("metaVitorias") == 3
    assert cfg.get("modoSessao") == "vitorias"
    assert cfg.get("ehDesafio") is True
    assert D["estadoSala"] == "aguardando"


def test_api_desafio_entrar_segunda_pessoa(cliente):
    C = cliente.post("/api/desafio/criar").json()
    E = cliente.post(
        "/api/sala/entrar",
        json={
            "codigoSala": C["codigoSala"],
            "nomeJogador": "Convidado",
        },
    )
    assert E.status_code == 200
    D = E.json()
    assert D["codigoSala"] == C["codigoSala"]
    assert D["idJogador"] != C["idJogador"]


def test_api_partida_retomar_com_token(cliente):
    C = cliente.post("/api/desafio/criar").json()
    R = cliente.get(
        f"/api/partida/{C['idPartida']}/retomar",
        params={"token": C["tokenSessao"], "id_jogador": C["idJogador"]},
    )
    assert R.status_code == 200
    D = R.json()
    assert D["codigoSala"] == C["codigoSala"]
    assert D["tokenSessao"] == C["tokenSessao"]


def test_api_sala_criar_tem_id_partida(cliente):
    R = cliente.post(
        "/api/sala/criar",
        json={
            "nomeJogador": "Host",
            "maximoJogadores": 4,
            "modoSessao": "pontos",
        },
    )
    assert R.status_code == 200
    D = R.json()
    assert D["idPartida"]
    uuid.UUID(D["idPartida"])
    assert D["tokenSessao"]
