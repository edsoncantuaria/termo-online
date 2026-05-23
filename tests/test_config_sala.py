"""Configuração da sala na espera (host)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas


def test_host_nao_pode_reduzir_maximo_abaixo_da_ocupacao():
    G = GerenciadorSalas()
    Sala, Host = G.CriarSala("host", ConfiguracaoSala(MaximoJogadores=4))
    G.EntrarSala(Sala.CodigoSala, "convidado", None, False)

    Erro = G.AtualizarConfiguracaoSala(
        Sala,
        Host.IdJogador,
        True,
        True,
        1,
        180,
        "pontos",
        5,
        False,
    )
    assert Erro is not None
    assert "não pode ser menor" in Erro


def test_info_convite_detecta_sala_cheia():
    G = GerenciadorSalas()
    Sala, _ = G.CriarSala("host", ConfiguracaoSala(MaximoJogadores=2))
    G.EntrarSala(Sala.CodigoSala, "p2", None, False)
    Info = G.InfoConviteSala(Sala.CodigoSala)
    assert Info is not None
    assert Info["cheia"] is True


def test_host_atualiza_senha_e_modo():
    G = GerenciadorSalas()
    Sala, Host = G.CriarSala("host", ConfiguracaoSala(MaximoJogadores=4))

    Erro = G.AtualizarConfiguracaoSala(
        Sala,
        Host.IdJogador,
        False,
        True,
        4,
        300,
        "vitorias",
        7,
        True,
        SenhaNova="abc",
        RemoverSenha=False,
    )
    assert Erro is None
    C = Sala.Configuracao
    assert C.MesmaPalavra is False
    assert C.VerOutros is True
    assert C.Senha == "abc"
    assert C.ModoSessao == "vitorias"
    assert C.MetaVitorias == 7
    assert C.TempoLimiteSegundos == 300
    assert C.InicioAutoDois is True
    assert C.SalaPublica is False
