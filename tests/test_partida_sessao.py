"""Testes de sessão de partida online (idPartida, token, pausa, desistência)."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo.partida_sessao import (
    ABANDONO_TOTAL_SEG,
    DesistirPartida,
    PAUSA_DESAFIO_SEG,
    RetomarPartida,
    ValidarTokenJogador,
    VerificarAbandonosProlongados,
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


def test_pausa_expirada_continua_ranqueada(Gerenciador):
    G, Sala, J1, J2 = Gerenciador
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    VerificarPausasExpiradas(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert not Sala.PartidaEncerrada
    assert Sala.EstadoSala == "jogando"
    J1Atual = Sala.Jogadores[J1.IdJogador]
    assert J1Atual.AusenteContinua
    assert J1Atual.Finalizou


def test_abandono_3min_ranqueada(Gerenciador):
    G, Sala, J1, J2 = Gerenciador
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    VerificarPausasExpiradas(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.Jogadores[J1.IdJogador].DesconexaoInicioEpoch = (
        time.time() - ABANDONO_TOTAL_SEG - 1
    )
    VerificarAbandonosProlongados(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.PartidaEncerrada
    assert Sala.VencedorId == J2.IdJogador


@pytest.fixture
def GerenciadorDesafio():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=4,
        ModoSessao=ModoVitorias,
        MetaVitorias=3,
        EhDesafio=True,
        InicioAutoDois=True,
        TempoLimiteSegundos=180,
    )
    Sala, J1 = G.CriarSala("Host", Config)
    _Sala2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Beta")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    ErroIni = G.IniciarPartida(Sala, J1.IdJogador)
    assert ErroIni is None
    Sala = G.ObterSala(Sala.CodigoSala)
    return G, Sala, J1, J2


def test_pausa_desafio_30_segundos(GerenciadorDesafio):
    G, Sala, J1, _J2 = GerenciadorDesafio
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == "pausada"
    assert int(Sala.PausaAteEpoch - time.time()) <= PAUSA_DESAFIO_SEG + 1


def test_pausa_desafio_expirada_continua_jogo(GerenciadorDesafio):
    G, Sala, J1, _J2 = GerenciadorDesafio
    G.MarcarConexao(Sala, J1.IdJogador, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    VerificarPausasExpiradas(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == "jogando"
    assert Sala.Jogadores[J1.IdJogador].AusenteContinua
    assert not Sala.PartidaEncerrada


def test_reconexao_limpa_ausente_continua(GerenciadorDesafio):
    G, Sala, J1, _J2 = GerenciadorDesafio
    Sala.Jogadores[J1.IdJogador].AusenteContinua = True
    Sala.Jogadores[J1.IdJogador].DesconexaoInicioEpoch = time.time()
    G.MarcarConexao(Sala, J1.IdJogador, True)
    Sala = G.ObterSala(Sala.CodigoSala)
    J = Sala.Jogadores[J1.IdJogador]
    assert not J.AusenteContinua
    assert J.DesconexaoInicioEpoch is None


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
