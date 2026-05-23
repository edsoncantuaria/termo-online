"""Tempo oficial do servidor (Brasília)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.tempo_brasil import DataHojeIsoBrasil, InfoTempoServidor
from servidor.aplicacao import CriarAplicacao


def test_info_tempo_servidor_tem_data_brasil():
    Info = InfoTempoServidor()
    assert Info["dataDiaBrasil"] == DataHojeIsoBrasil()
    assert Info["segundosAteMeiaNoiteBrasil"] > 0
    assert Info["fuso"] == "America/Sao_Paulo"


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "tempo.db")
    persistencia.InicializarBanco()
    return TestClient(CriarAplicacao())


def test_api_tempo(cliente):
    R = cliente.get("/api/tempo")
    assert R.status_code == 200
    D = R.json()
    assert D["dataDiaBrasil"] == DataHojeIsoBrasil()


def test_health_inclui_data_brasil(cliente):
    R = cliente.get("/api/health")
    assert R.status_code == 200
    assert R.json()["dataDiaBrasil"] == DataHojeIsoBrasil()
