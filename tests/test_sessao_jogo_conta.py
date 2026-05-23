"""Sessão de jogo ativa por conta no banco."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo import persistencia
from nucleo.sessao_jogo_conta import (
    MontarJogoAtivoParaConta,
    SincronizarSessoesContaDaSala,
)


def test_sincronizar_e_consultar_jogo_ativo_ranqueada(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "sessao.db")
    persistencia.InicializarBanco()

    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        Ranqueada=True,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
        InicioAutoDois=True,
    )
    Sala, J1 = G.CriarSala("Eu", Config, IdConta="conta-a")
    _S2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Rival", IdConta="conta-b")
    assert Erro is None
    G.IniciarDueloRanqueado(Sala)
    Sala = G.ObterSala(Sala.CodigoSala)
    G.PersistirSala(Sala)

    Jogo = MontarJogoAtivoParaConta(G, "conta-a")
    assert Jogo is not None
    assert Jogo["ativo"] is True
    assert Jogo["tipo"] == "ranqueada"
    assert Jogo["codigoSala"] == Sala.CodigoSala
    assert Jogo["estadoSala"] == "jogando"


def test_limpar_ao_encerrar_sala(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "sessao2.db")
    persistencia.InicializarBanco()

    G = GerenciadorSalas()
    Config = ConfiguracaoSala(MaximoJogadores=2, InicioAutoDois=True)
    Sala, J1 = G.CriarSala("H", Config, IdConta="conta-x")
    G.PersistirSala(Sala)
    persistencia.SalvarSessaoJogoConta(
        IdConta="conta-x",
        Tipo="arena",
        IdPartida=Sala.IdPartida,
        CodigoSala=Sala.CodigoSala,
        IdJogador=J1.IdJogador,
        EstadoSala="aguardando",
    )
    Sala.PartidaEncerrada = True
    SincronizarSessoesContaDaSala(G, Sala)
    assert persistencia.ObterSessaoJogoConta("conta-x") is None
