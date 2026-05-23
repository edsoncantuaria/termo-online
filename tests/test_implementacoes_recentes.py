"""Testes das implementações recentes: desafio, pausa, solo UUID, ranqueado competitivo."""

import re
import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import ModoVitorias
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas, JogadorSala
from nucleo.matchmaking import FilaMatchmaking
from nucleo.modos_solo import ModoDesafio, ModoDiaria, ModoDueto, ModoPratica, ModoQuarteto
from nucleo.partida_sessao import (
    ABANDONO_TOTAL_SEG,
    PAUSA_ARENA_SEG,
    PAUSA_DESAFIO_SEG,
    PAUSA_RANQUEADA_SEG,
    SegundosPausaSala,
    VerificarAbandonosProlongados,
    VerificarPausasExpiradas,
)
from nucleo.sala_persistencia import ExportarSnapshot, ImportarSnapshot
from servidor.partida_solo import NovaPartida
from nucleo.modos_solo import CriarTabuleiros


def _SalaComConfig(**Kw):
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(**Kw)
    Sala, _ = G.CriarSala("Host", Config)
    return G, Sala


def test_segundos_pausa_por_tipo_sala():
    _, Ranq = _SalaComConfig(Ranqueada=True)
    _, Desafio = _SalaComConfig(EhDesafio=True)
    _, Arena = _SalaComConfig()
    assert SegundosPausaSala(Ranq) == PAUSA_RANQUEADA_SEG
    assert SegundosPausaSala(Desafio) == PAUSA_DESAFIO_SEG
    assert SegundosPausaSala(Arena) == PAUSA_ARENA_SEG


def test_config_desafio_padrao_quatro_jogadores_tres_vitorias():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MesmaPalavra=True,
        VerOutros=True,
        MaximoJogadores=4,
        TempoLimiteSegundos=180,
        ModoSessao=ModoVitorias,
        MetaVitorias=3,
        InicioAutoDois=True,
        SalaPublica=False,
        EhDesafio=True,
    )
    Sala, Host = G.CriarSala("Host", Config)
    assert len(Sala.CodigoSala) == 6
    assert Sala.Configuracao.EhDesafio
    assert Sala.Configuracao.MaximoJogadores == 4
    assert Sala.Configuracao.MetaVitorias == 3
    assert Sala.Configuracao.ModoSessao == ModoVitorias
    assert Sala.IdPartida
    assert Host.TokenSessao


def test_desafio_pausa_continua_e_remove_apos_3min():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=4,
        ModoSessao=ModoVitorias,
        MetaVitorias=3,
        EhDesafio=True,
        InicioAutoDois=True,
    )
    Sala, J1 = G.CriarSala("H", Config)
    G.EntrarSala(Sala.CodigoSala, "P2")
    G.EntrarSala(Sala.CodigoSala, "P3")
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    G.IniciarPartida(Sala, Sala.CriadorId)
    Sala = G.ObterSala(Sala.CodigoSala)
    IdAusente = Sala.CriadorId

    G.MarcarConexao(Sala, IdAusente, False)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.PausaAteEpoch = time.time() - 1
    VerificarPausasExpiradas(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert Sala.EstadoSala == "jogando"
    assert Sala.Jogadores[IdAusente].AusenteContinua
    assert Sala.Jogadores[IdAusente].Finalizou
    assert not Sala.PartidaEncerrada

    Sala.Jogadores[IdAusente].DesconexaoInicioEpoch = (
        time.time() - ABANDONO_TOTAL_SEG - 1
    )
    VerificarAbandonosProlongados(G)
    Sala = G.ObterSala(Sala.CodigoSala)
    assert IdAusente not in Sala.Jogadores
    assert not Sala.PartidaEncerrada


@pytest.mark.parametrize(
    "modo",
    [ModoPratica, ModoDiaria, ModoDueto, ModoQuarteto, ModoDesafio],
)
def test_solo_modos_recebem_uuid(modo):
    Kw = {}
    if modo == ModoDesafio:
        Kw["CodigoDesafio"] = "TEST01"
    if modo == ModoDiaria:
        Kw["DataDia"] = "2099-01-01"
    Tabs = CriarTabuleiros(modo, "normal", Kw.get("CodigoDesafio"))
    Partida = NovaPartida(
        PalavraSecreta=Tabs[0]["palavraSecreta"],
        PalavraComAcento=Tabs[0]["palavraComAcento"],
        Modo=modo,
        Tabuleiros=Tabs,
        **{k: v for k, v in Kw.items() if k != "CodigoDesafio"},
        CodigoDesafio=Kw.get("CodigoDesafio"),
    )
    assert Partida.IdPartida
    uuid.UUID(Partida.IdPartida)
    assert Partida.TokenPartida
    assert len(Partida.TokenPartida) >= 16


def test_bot_id_publico_nao_revela_bot():
    G = GerenciadorSalas()
    Bot = JogadorSala(IdJogador="bot-bot_001", NomeJogador="rival", EhBot=True)
    Pub = G.IdJogadorPublico(Bot)
    assert "bot" not in Pub.lower()
    assert re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        Pub,
    )


def test_snapshot_persiste_desafio_e_ausente():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(EhDesafio=True, MaximoJogadores=4, MetaVitorias=3)
    Sala, J = G.CriarSala("H", Config)
    J.AusenteContinua = True
    J.DesconexaoInicioEpoch = time.time()
    Snap = ExportarSnapshot(Sala)
    assert Snap["configuracao"]["ehDesafio"] is True
    assert Snap["jogadores"][0]["ausenteContinua"] is True
    assert Snap["jogadores"][0]["desconexaoInicioEpoch"]

    Restaurada = ImportarSnapshot(Snap)
    assert Restaurada is not None
    Jr = Restaurada.Jogadores[J.IdJogador]
    assert Restaurada.Configuracao.EhDesafio
    assert Jr.AusenteContinua
    assert Jr.DesconexaoInicioEpoch


def test_finalizar_ausentes_rodada_atual():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(
        MaximoJogadores=2,
        ModoSessao=ModoVitorias,
        MetaVitorias=1,
        InicioAutoDois=True,
    )
    Sala, J1 = G.CriarSala("A", Config)
    _Sala2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "B")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    G.IniciarPartida(Sala, J1.IdJogador)
    Sala = G.ObterSala(Sala.CodigoSala)
    Sala.Jogadores[J2.IdJogador].AusenteContinua = True
    Sala.Jogadores[J2.IdJogador].Finalizou = False
    assert G.FinalizarAusentesRodadaAtual(Sala)
    assert Sala.Jogadores[J2.IdJogador].Finalizou


def test_matchmaking_inicia_duelo_em_jogando():
    from nucleo.matchmaking import EntradaFila, FilaMatchmaking

    G = GerenciadorSalas()
    Fila = FilaMatchmaking()
    Fila.Fila["c1"] = EntradaFila(IdConta="c1", Nick="alfa", Pontos=500)
    Fila.Fila["c2"] = EntradaFila(IdConta="c2", Nick="beta", Pontos=520)
    Fila.Processar(G)
    assert "c1" not in Fila.Fila
    Match = Fila.UltimoMatch.get("c1")
    assert Match
    Sala = G.ObterSala(Match["codigoSala"])
    assert Sala is not None
    assert Sala.EstadoSala == "jogando"
    assert Match["idPartida"]
    assert Match["tokenSessao"]


def test_matchmaking_config_ranqueada_ver_outros_false():
    Fila = FilaMatchmaking()
    Config = Fila._ConfigRanqueada()
    assert Config.VerOutros is False
    assert Config.Ranqueada is True


def test_estado_publico_ranqueado_oponente_modo_competitivo():
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
    _Sala2, J2, Erro = G.EntrarSala(Sala.CodigoSala, "Rival")
    assert Erro is None
    Sala = G.ObterSala(Sala.CodigoSala)
    for J in G.JogadoresAtivos(Sala):
        J.Pronto = True
    G.IniciarPartida(Sala, J1.IdJogador)
    Sala = G.ObterSala(Sala.CodigoSala)
    Estado = G.EstadoPublicoSala(Sala, J1.IdJogador)
    Oponente = next(j for j in Estado["jogadores"] if not j["souEu"])
    assert Oponente["modoCompetitivo"] is True
    assert Oponente["tentativas"] == []
    assert "jaChutou" in Oponente
