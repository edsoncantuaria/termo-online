import copy
import time

from nucleo.bots_ranqueados import (
    BOTS,
    ContarBotsDisponiveis,
    ContarBotsPorElo,
    ELOS_COM_BOTS,
    EscolherBotParaPontos,
    LiberarReservaBot,
    MINIMOS_BOTS_POR_ELO,
    RP_MAXIMO_BOTS,
    ReservarBot,
    TOTAL_BOTS,
)
from nucleo.ranqueada import EloDePontos
from nucleo.matchmaking import FilaMatchmaking
from nucleo.matchmaking_competitivo import BUSCA_REAL_SEG, ESPERA_BOT_SEG
from nucleo.ranking_ranqueado import MontarRankingCompleto


def test_cem_bots_com_rp_minimo_zero():
    assert len(BOTS) == TOTAL_BOTS == 100
    assert min(B.Pontos for B in BOTS) >= 0
    assert ContarBotsDisponiveis() == 100


def test_bots_distribuidos_nos_elos_baixos():
    PorElo = ContarBotsPorElo()
    for Elo, Minimo in MINIMOS_BOTS_POR_ELO.items():
        assert PorElo.get(Elo, 0) >= Minimo, f"poucos bots em {Elo}: {PorElo.get(Elo, 0)}"
    assert PorElo["papelao"] >= 20
    assert PorElo["madeira"] >= 14
    assert PorElo.get("prata", 0) == 0
    assert PorElo.get("ouro", 0) == 0
    assert PorElo.get("platina", 0) == 0
    assert PorElo.get("diamante", 0) == 0
    assert PorElo.get("estrela", 0) == 0


def test_nenhum_bot_ouro_para_cima():
    assert ELOS_COM_BOTS == frozenset({"papelao", "madeira", "ferro", "bronze"})
    for B in BOTS:
        assert B.Pontos <= RP_MAXIMO_BOTS
        assert EloDePontos(B.Pontos) in ELOS_COM_BOTS


def test_escolher_bot_para_jogador_iniciante():
    Bot = EscolherBotParaPontos(0, SegundosEspera=14.0)
    assert Bot is not None
    assert abs(Bot.Pontos - 0) <= 200
    assert EloDePontos(Bot.Pontos) in ("papelao", "madeira", "ferro", "bronze")


def test_bot_reserva_e_libera():
    Bot = EscolherBotParaPontos(500)
    assert Bot is not None
    ReservarBot(Bot.Id)
    assert ContarBotsDisponiveis() == 99
    LiberarReservaBot(Bot.Id)
    assert ContarBotsDisponiveis() == 100


class _ArmazemFilaCopia:
    """Simula Redis: cada leitura devolve cópia — exige regravar após mutar."""

    def __init__(self) -> None:
        self._d: dict = {}

    def get(self, Chave, Padrao=None):
        Valor = self._d.get(Chave)
        return copy.copy(Valor) if Valor is not None else Padrao

    def __contains__(self, Chave: str) -> bool:
        return Chave in self._d

    def __setitem__(self, Chave, Valor) -> None:
        self._d[Chave] = Valor

    def keys(self):
        return list(self._d.keys())

    def pop(self, Chave, Padrao=None):
        return self._d.pop(Chave, Padrao)

    def __len__(self) -> int:
        return len(self._d)


class GerenciadorFake:
    Salas = {}

    def CriarSala(self, *a, **k):
        from nucleo.gerenciador_salas import GerenciadorSalas

        return GerenciadorSalas().CriarSala(*a, **k)

    def ObterSala(self, c):
        return self.Salas.get(c)

    def IniciarDueloRanqueado(self, s):
        pass

    def TentarInicioAutomatico(self, s):
        pass

    def PersistirSala(self, s):
        self.Salas[s.CodigoSala] = s


def test_fila_persiste_reserva_bot_como_redis(monkeypatch):
    from nucleo import matchmaking as mm

    G = GerenciadorFake()
    Fila = FilaMatchmaking()
    Fila.Fila = _ArmazemFilaCopia()
    T0 = 2000.0
    monkeypatch.setattr(mm.time, "time", lambda: T0)
    Fila.Fila["u1"] = mm.EntradaFila(
        IdConta="u1", Nick="tester", Pontos=400, EntrouEm=T0
    )
    monkeypatch.setattr(
        mm.time, "time", lambda: T0 + BUSCA_REAL_SEG + 0.2
    )
    Fila.Processar(G)
    assert Fila.Fila.get("u1").BotReservadoId


def test_fila_entra_bot_apos_tempo_configurado(monkeypatch):
    from nucleo import matchmaking as mm

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
