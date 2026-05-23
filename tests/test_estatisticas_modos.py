"""Estatísticas por modo no perfil."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.estatisticas import MontarListaPartidasPorModo, ObterEstatisticasJogador
from nucleo.modos_solo import ModoDueto, ModoPratica
from servidor.partida_solo import NovaPartida, SalvarPartida


def test_contar_partidas_solo_por_modo(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "test.db")
    persistencia.InicializarBanco()
    P1 = NovaPartida(
        PalavraSecreta="abcde",
        PalavraComAcento="abcde",
        Modo=ModoPratica,
        Tabuleiros=[],
        NomeJogador="statsmodo",
    )
    P1.Encerrada = True
    P1.Venceu = True
    SalvarPartida(P1)

    P2 = NovaPartida(
        PalavraSecreta="fghij",
        PalavraComAcento="fghij",
        Modo=ModoDueto,
        Tabuleiros=[],
        NomeJogador="statsmodo",
    )
    P2.Encerrada = True
    P2.Venceu = False
    SalvarPartida(P2)

    Contagem = persistencia.ContarPartidasSoloPorModo(None, "statsmodo")
    assert Contagem[ModoPratica]["partidas"] >= 1
    assert Contagem[ModoDueto]["partidas"] >= 1

    Lista = MontarListaPartidasPorModo(Contagem, 3, 1)
    Pratica = next(x for x in Lista if x["modo"] == ModoPratica)
    Ranq = next(x for x in Lista if x["modo"] == "ranqueada")
    assert Pratica["partidas"] >= 1
    assert Ranq["partidas"] == 3
    assert Ranq["vitorias"] == 1

    Stats = ObterEstatisticasJogador("statsmodo")
    assert "partidasPorModo" in Stats
    assert len(Stats["partidasPorModo"]) == 6
