"""Ranqueado: visibilidade competitiva, online na fila e disfarce de bots."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas, JogadorSala
from nucleo.logica_jogo import AvaliarChute
from nucleo.matchmaking import FilaMatchmaking, JogadoresOnlineParaCliente, MIN_JOGADORES_ONLINE_EXIBIR


@pytest.fixture
def DueloRanqueado():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        Ranqueada=True,
        VerOutros=False,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
        InicioAutoDois=True,
    )
    Sala, J1 = G.CriarSala("Eu", Config)
    J2 = JogadorSala(
        IdJogador="bot-interno",
        NomeJogador="Rival",
        EhBot=True,
        Conectado=True,
    )
    Sala.Jogadores[J2.IdJogador] = J2
    G.AtribuirPalavras(Sala)
    Palavra, _ = G.ObterPalavraJogador(Sala, J2)
    J2.Tentativas.append({"letras": AvaliarChute(Palavra, "aaaaa")})
    Sala.EstadoSala = "jogando"
    return G, Sala, J1, J2


def test_oponente_ranqueado_so_revela_se_chutou(DueloRanqueado):
    G, Sala, J1, J2 = DueloRanqueado
    Pub = G.SerializarJogador(Sala, J2, J1.IdJogador, False)
    assert Pub["modoCompetitivo"] is True
    assert Pub["jaChutou"] is True
    assert Pub["tentativas"] == []
    assert Pub["tentativasUsadas"] == 1
    assert Pub["venceu"] is False


def test_jogadores_online_null_abaixo_do_minimo(monkeypatch):
    from nucleo import matchmaking as mm

    monkeypatch.setattr(mm, "ContarConexoesWsLobby", lambda: 10)
    monkeypatch.setattr(mm, "ContarConexoesWsSala", lambda: 5)
    assert JogadoresOnlineParaCliente() is None


def test_jogadores_online_exibe_acima_do_minimo(monkeypatch):
    from nucleo import matchmaking as mm

    Total = MIN_JOGADORES_ONLINE_EXIBIR + 10
    monkeypatch.setattr(mm, "ContarConexoesWsLobby", lambda: Total // 2)
    monkeypatch.setattr(mm, "ContarConexoesWsSala", lambda: Total - Total // 2)
    assert JogadoresOnlineParaCliente() == Total


def test_status_fila_sem_inflar_com_bots(monkeypatch):
    from nucleo import matchmaking as mm

    monkeypatch.setattr(mm, "ContarConexoesWsLobby", lambda: 0)
    monkeypatch.setattr(mm, "ContarConexoesWsSala", lambda: 0)
    Fila = FilaMatchmaking()
    Fila.Fila["c1"] = mm.EntradaFila(IdConta="c1", Nick="a", Pontos=500)
    D = Fila.Status("c1")
    assert D["estado"] == "aguardando"
    assert D["jogadoresOnline"] is None
