"""Retomada de partida ranqueada após persistência (simula reinício do servidor)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo.partida_sessao import DesistirPartida, IdPartidaValido, RetomarPartida


@pytest.fixture
def DueloRanqueado(tmp_path, monkeypatch):
    from nucleo import persistencia

    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "termo_test.db")
    persistencia.InicializarBanco()
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        InicioAutoDois=True,
        Ranqueada=True,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
    )
    Sala, J1 = G.CriarSala("Alpha", Config, IdConta="conta-a")
    _S2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Beta", IdConta="conta-b")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    assert G.IniciarPartida(Sala, J1.IdJogador) is None
    return G, G.ObterSala(Sala.CodigoSala), J1, J2


def test_id_partida_valido_uuid():
    assert IdPartidaValido("00000000-0000-4000-8000-000000000001") is True
    assert IdPartidaValido("nao-uuid") is False
    assert IdPartidaValido("") is False


def test_retomar_apos_encerrar_com_novo_gerenciador(DueloRanqueado):
    G1, Sala, J1, _J2 = DueloRanqueado
    IdPartida = Sala.IdPartida
    Token = J1.TokenSessao
    IdJogador = J1.IdJogador

    _Dados, Erro, Status = DesistirPartida(G1, IdPartida, IdJogador, Token)
    assert Status == 200 and Erro is None

    G1.Salas.clear()

    G2 = GerenciadorSalas()
    Dados, Erro2, Status2 = RetomarPartida(G2, IdPartida, Token, IdJogador)
    assert Status2 == 200, Erro2
    assert Dados["partidaEncerrada"] is True
    assert Dados["podeRetomar"] is False
    assert Dados["codigoSala"] == Sala.CodigoSala
