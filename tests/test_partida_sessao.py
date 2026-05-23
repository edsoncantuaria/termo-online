"""Testes de sessão de partida online (idPartida, token, pausa, desistência)."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo.partida_sessao import (
    DesistirPartida,
    RetomarPartida,
    ValidarTokenJogador,
    VerificarPausasExpiradas,
)


@pytest.fixture
def Gerenciador():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        InicioAutoDois=True,
        Ranqueada=True,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
    )
    Sala, J1 = G.CriarSala("Alpha", Config)
    _Sala2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Beta")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    ErroIni = G.IniciarPartida(Sala, J1.IdJogador)
    assert ErroIni is None
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == "jogando"
    return G, Sala, J1, J2


def test_criar_sala_retorna_id_partida_e_token(Gerenciador):
    G, Sala, J1, _J2 = Gerenciador
    assert Sala.IdPartida
    assert J1.TokenSessao
    assert ValidarTokenJogador(J1, J1.TokenSessao)


def test_retomar_partida_com_token(Gerenciador):
    G, Sala, J1, _J2 = Gerenciador
    Dados, Erro, Status = RetomarPartida(
        G, Sala.IdPartida, J1.TokenSessao, J1.IdJogador
    )
    assert Status == 200
    assert Erro is None
    assert Dados["codigoSala"] == Sala.CodigoSala
    assert Dados["idPartida"] == Sala.IdPartida
    assert Dados["tokenSessao"] == J1.TokenSessao


def test_retomar_rejeita_token_invalido(Gerenciador):
    G, Sala, J1, _J2 = Gerenciador
    _Dados, Erro, Status = RetomarPartida(
        G, Sala.IdPartida, "token-invalido", J1.IdJogador
    )
    assert Status == 403
    assert Erro


def test_pausa_ranqueada_ao_desconectar(Gerenciador):
    G, Sala, J1, J2 = Gerenciador
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == "pausada"
    assert Sala.IdJogadorPausado == J1.IdJogador
    assert Sala.PausaAteEpoch
    J2Atual = Sala.Jogadores[J2.IdJogador]
    assert J2Atual.TempoFimEpoch is None or Sala.TimersCongelados.get(J2.IdJogador)


def test_reconexao_cancela_pausa(Gerenciador):
    G, Sala, J1, _J2 = Gerenciador
    Antes = Sala.EstadoSalaAntesPausa or "jogando"
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    G.MarcarConexao(Sala, J1.IdJogador, True)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == Antes
    assert Sala.IdJogadorPausado is None


def test_pausa_expirada_encerra_ranqueada(Gerenciador):
    G, Sala, J1, J2 = Gerenciador
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    VerificarPausasExpiradas(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.PartidaEncerrada
    assert Sala.VencedorId == J2.IdJogador


def test_desistir_partida_ranqueada(Gerenciador):
    G, Sala, J1, J2 = Gerenciador
    Dados, Erro, Status = DesistirPartida(
        G, Sala.IdPartida, J1.IdJogador, J1.TokenSessao
    )
    assert Status == 200
    assert Erro is None
    assert Dados["desistiu"] is True
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.PartidaEncerrada
    assert Sala.VencedorId == J2.IdJogador
