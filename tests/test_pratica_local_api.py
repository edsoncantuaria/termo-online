"""Prática não usa mais API de partida solo."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from servidor.aplicacao import CriarAplicacao


def test_iniciar_pratica_rejeitada_na_api(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "pr.db")
    persistencia.InicializarBanco()
    Cliente = TestClient(CriarAplicacao())
    R = Cliente.post(
        "/api/jogar/iniciar",
        json={"nomeJogador": "teste", "modo": "pratica"},
    )
    assert R.status_code == 410


def test_estatisticas_sem_linha_pratica(tmp_path, monkeypatch):
    from nucleo.estatisticas import MontarListaPartidasPorModo
    from nucleo.modos_solo import ModoPratica

    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "st.db")
    persistencia.InicializarBanco()
    Lista = MontarListaPartidasPorModo({ModoPratica: {"partidas": 9, "vitorias": 3}})
    Modos = {x["modo"] for x in Lista}
    assert ModoPratica not in Modos
