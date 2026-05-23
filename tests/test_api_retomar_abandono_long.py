"""HTTP GET /partida/retomar após abandono prolongado (cenário longo)."""

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo.partida_sessao import ABANDONO_TOTAL_SEG, ProcessarSalasComJogadoresOffline
from servidor.aplicacao import CriarAplicacao
from servidor.estado_global import GerenciadorVersus


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "aband.db")
    persistencia.InicializarBanco()
    GerenciadorVersus.Salas.clear()
    return TestClient(CriarAplicacao())


def test_api_retomar_apos_abandono_simulado(cliente):
    G = GerenciadorVersus
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        InicioAutoDois=True,
        Ranqueada=True,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
    )
    Sala, J1 = G.CriarSala("Host", Config)
    _S, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Guest")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    assert G.IniciarPartida(Sala, J1.IdJogador) is None

    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    ProcessarSalasComJogadoresOffline(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.Jogadores[J1.IdJogador].DesconexaoInicioEpoch = (
        time.time() - ABANDONO_TOTAL_SEG - 1
    )
    ProcessarSalasComJogadoresOffline(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.PartidaEncerrada

    R = cliente.get(
        f"/api/partida/{Sala.IdPartida}/retomar",
        params={"token": J1.TokenSessao, "id_jogador": J1.IdJogador},
    )
    assert R.status_code == 200
    D = R.json()
    assert D["partidaEncerrada"] is True
    assert D["somenteResultado"] is True
    assert D["vocePerdeu"] is True
    assert D["vencedorId"] == J2.IdJogador
