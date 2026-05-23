"""Busca de perfil público por nick."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient

from nucleo import persistencia
from nucleo.contas import EntrarComoVisitante, RegistrarConta
from nucleo.ranking_ranqueado import MontarRankingCompleto
from nucleo.modos_solo import ModoPratica
from nucleo.bots_ranqueados import BOTS
from nucleo.perfil_publico import BuscarPerfilJogador
from nucleo.ranqueada import RegistrarDueloRanqueadoVsBot
from servidor.aplicacao import CriarAplicacao
from servidor.partida_solo import NovaPartida, SalvarPartida


def test_perfil_registrado_com_partidas(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "pub.db")
    persistencia.InicializarBanco()
    Perfil, _ = RegistrarConta("jogpub", "jogpub@test.com", "senha123")
    Id = Perfil["idConta"]

    P = NovaPartida(
        PalavraSecreta="abcde",
        PalavraComAcento="abcde",
        Modo=ModoPratica,
        Tabuleiros=[],
        NomeJogador="jogpub",
    )
    P.IdConta = Id
    P.Encerrada = True
    P.Venceu = True
    SalvarPartida(P)

    D = BuscarPerfilJogador("jogpub")
    assert D["tipo"] == "registrado"
    assert D["perfil"]["vitoriasRanqueadas"] >= 0
    assert len(D["ultimasPartidas"]) >= 1
    assert D["limitePartidas"] == 20


def test_perfil_visitante_sem_conta(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "vis.db")
    persistencia.InicializarBanco()

    D = BuscarPerfilJogador("apelidox")
    assert D["tipo"] == "visitante"
    assert D["mensagem"]
    assert D["estatisticas"] is None
    assert D["ultimasPartidas"] == []
    assert D["posicaoRanqueada"] is None
    assert D["encontrado"] is False


def test_perfil_conta_visitante_so_mensagem(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "visconta.db")
    persistencia.InicializarBanco()
    EntrarComoVisitante("visitbusca")

    D = BuscarPerfilJogador("visitbusca")
    assert D["tipo"] == "visitante"
    assert D["encontrado"] is True
    assert D["estatisticas"] is None
    assert D["ultimasPartidas"] == []
    assert "visitante" in D["mensagem"].lower()


def test_perfil_registrado_tem_posicao_rank(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "pos.db")
    persistencia.InicializarBanco()
    RegistrarConta("rankpos", "rankpos@test.com", "senha123")

    D = BuscarPerfilJogador("rankpos")
    assert D["tipo"] == "registrado"
    assert D["posicaoRanqueada"] is not None
    assert D["posicaoRanqueada"] >= 1
    assert D["totalRanqueados"] == MontarRankingCompleto({"nick": "rankpos"})[
        "totalRanqueados"
    ]


def test_perfil_bot_como_jogador_real(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "bot.db")
    persistencia.InicializarBanco()
    PerfilHum, _ = RegistrarConta("humano1", "hum1@test.com", "senha123")
    Bot = BOTS[0]
    RegistrarDueloRanqueadoVsBot(
        PerfilHum["idConta"],
        True,
        Bot.Pontos,
        CodigoSala="SALA1",
        IdPartida="part-bot-1",
        IdJogadorBot=f"bot-{Bot.Id}",
    )

    D = BuscarPerfilJogador(Bot.Nick)
    assert D["tipo"] == "registrado"
    assert D["mensagem"] is None
    assert D["perfil"]["ehVisitante"] is False
    assert D["perfil"]["partidasRanqueadas"] >= 1
    assert len(D["ultimasPartidas"]) >= 1
    assert D["ultimasPartidas"][0]["oponente"] == "humano1"
    assert "Bot" not in str(D["ultimasPartidas"])


def test_api_perfil_jogador(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "api.db")
    persistencia.InicializarBanco()
    _, Token = RegistrarConta("buscador", "busc@test.com", "senha123")
    RegistrarConta("alvo", "alvo@test.com", "senha456")

    Cliente = TestClient(CriarAplicacao())
    R = Cliente.get(
        "/api/jogador/alvo/perfil",
        headers={"Authorization": f"Bearer {Token}"},
    )
    assert R.status_code == 200
    assert R.json()["tipo"] == "registrado"
    assert len(R.json()["ultimasPartidas"]) <= 20
