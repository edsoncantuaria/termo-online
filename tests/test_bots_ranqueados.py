import time

from nucleo.bots_ranqueados import (
    BOTS,
    ContarBotsDisponiveis,
    EscolherBotParaPontos,
    LiberarReservaBot,
    ReservarBot,
    TOTAL_BOTS,
)
from nucleo.matchmaking import FilaMatchmaking
from nucleo.matchmaking_competitivo import BUSCA_REAL_SEG, ESPERA_BOT_SEG
from nucleo.ranking_ranqueado import MontarRankingCompleto


def test_cem_bots_com_rp_minimo_zero():
    assert len(BOTS) == TOTAL_BOTS == 100
    assert min(B.Pontos for B in BOTS) >= 0
    assert ContarBotsDisponiveis() == 100


def test_bot_reserva_e_libera():
    Bot = EscolherBotParaPontos(500)
    assert Bot is not None
    ReservarBot(Bot.Id)
    assert ContarBotsDisponiveis() == 99
    LiberarReservaBot(Bot.Id)
    assert ContarBotsDisponiveis() == 100


def test_fila_entra_bot_apos_14_segundos(monkeypatch):
    from nucleo import matchmaking as mm

    class GerenciadorFake:
        Salas = {}

        def CriarSala(self, *a, **k):
            from nucleo.gerenciador_salas import GerenciadorSalas

            return GerenciadorSalas().CriarSala(*a, **k)

        def ObterSala(self, c):
            return self.Salas.get(c)

        def TentarInicioAutomatico(self, s):
            pass

        def PersistirSala(self, s):
            self.Salas[s.CodigoSala] = s

    G = GerenciadorFake()
    Fila = FilaMatchmaking()
    T0 = 1000.0
    monkeypatch.setattr(mm.time, "time", lambda: T0)
    Fila.Fila["u1"] = mm.EntradaFila(
        IdConta="u1", Nick="tester", Pontos=400, EntrouEm=T0
    )
    Fila.Processar(G)
    assert "u1" in Fila.Fila
    monkeypatch.setattr(mm.time, "time", lambda: T0 + BUSCA_REAL_SEG + 0.1)
    Fila.Processar(G)
    assert Fila.Fila["u1"].BotReservadoId
    monkeypatch.setattr(
        mm.time, "time", lambda: T0 + BUSCA_REAL_SEG + ESPERA_BOT_SEG + 0.1
    )
    Fila.Processar(G)
    assert "u1" not in Fila.Fila
    assert "u1" in Fila.UltimoMatch
    assert "oponenteEhBot" not in Fila.UltimoMatch["u1"]


def test_ranking_inclui_bots_sem_expor_ao_cliente():
    D = MontarRankingCompleto({"nick": "zzz_inexistente", "ehVisitante": False, "pontosRanqueada": 0})
    assert D["totalRanqueados"] >= 2000
    assert "totalBots" not in D
    for R in D["ranking"]:
        assert "ehBot" not in R


def test_ranking_mostra_usuario_fora_do_topo():
    Perfil = {
        "nick": "zzz_rank_test_user",
        "ehVisitante": False,
        "pontosRanqueada": 0,
        "elo": "madeira",
        "eloNome": "Madeira",
        "partidasRanqueadas": 0,
        "vitoriasRanqueadas": 0,
    }
    D = MontarRankingCompleto(Perfil)
    assert D["minhaPosicao"] is not None
    assert D["minhaPosicao"] > 20
    Eu = [R for R in D["ranking"] if R.get("souEu")]
    assert len(Eu) == 1
    assert Eu[0]["posicao"] == D["minhaPosicao"]
    assert any(R.get("tipo") == "ellipsis" for R in D["ranking"])
