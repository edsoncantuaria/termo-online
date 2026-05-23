"""Chute de sala via HTTP (fallback ao WebSocket)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.gerenciador_salas import ConfiguracaoSala
from servidor.aplicacao import CriarAplicacao
from servidor.estado_global import GerenciadorVersus


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "chute.db")
    persistencia.InicializarBanco()
    GerenciadorVersus.Salas.clear()
    return TestClient(CriarAplicacao())


def test_chute_http_rejeita_fora_de_jogo(cliente):
    Config = ConfiguracaoSala(
        MesmaPalavra=True,
        VerOutros=True,
        MaximoJogadores=4,
        TempoLimiteSegundos=0,
        InicioAutoDois=True,
    )
    Sala, Jogador = GerenciadorVersus.CriarSala("host", Config)
    R = cliente.post(
        f"/api/sala/{Sala.CodigoSala}/chute",
        json={"idJogador": Jogador.IdJogador, "palavra": "termo"},
    )
    assert R.status_code == 200
    Corpo = R.json()
    assert Corpo["valido"] is False
    assert "rodada" in Corpo["mensagem"].lower()
