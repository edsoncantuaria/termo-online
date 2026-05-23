"""Histórico unificado de últimas partidas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient

from nucleo import persistencia
from nucleo.contas import RegistrarConta
from nucleo.modos_solo import ModoPratica
from servidor.aplicacao import CriarAplicacao
from servidor.partida_solo import NovaPartida, SalvarPartida


def test_listar_ultimas_partidas_mescla_solo_e_ranqueado(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "ult.db")
    persistencia.InicializarBanco()
    Id = persistencia.CriarConta("histpart", "h", "s", EhVisitante=False)

    P = NovaPartida(
        PalavraSecreta="abcde",
        PalavraComAcento="abcde",
        Modo=ModoPratica,
        Tabuleiros=[],
        NomeJogador="histpart",
    )
    P.IdConta = Id
    P.Encerrada = True
    P.Venceu = True
    SalvarPartida(P)

    persistencia.RegistrarHistoricoRanqueada(
        Id, "bot:teste", "SALA01", 10, 1000, 1010, True, "part-r1"
    )

    Lista = persistencia.ListarUltimasPartidasConta(Id, 20)
    assert len(Lista) <= 20
    Tipos = {X["tipo"] for X in Lista}
    assert "solo" in Tipos
    assert "ranqueada" in Tipos


def test_api_ultimas_partidas_limite_20(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "apiult.db")
    persistencia.InicializarBanco()
    _, Token = RegistrarConta("apihist", "apihist@test.com", "senha123")
    Cliente = TestClient(CriarAplicacao())

    R = Cliente.get(
        "/api/conta/ultimas-partidas",
        headers={"Authorization": f"Bearer {Token}"},
    )
    assert R.status_code == 200
    Corpo = R.json()
    assert Corpo["limite"] == 20
    assert len(Corpo["partidas"]) <= 20
