import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.arena_rodadas import (
    CalcularPontosRodada,
    ContarVerdesTentativa,
    DeterminarVencedorRodada,
    DeterminarVencedoresRodadaPorVerdes,
    MelhorContagemVerdes,
    ModoPontos,
    ModoVitorias,
    MontarMensagemFimRodada,
    MontarPlacar,
    SessaoAtingiuLimite,
)
from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas, JogadorSala, SalaJogo


def test_pontos_por_tentativa():
    assert CalcularPontosRodada(True, 1) == 6
    assert CalcularPontosRodada(True, 6) == 1
    assert CalcularPontosRodada(False, 3) == 0


def test_sessao_pontos_infinito():
    assert not SessaoAtingiuLimite(ModoPontos, 99, 0, {}, 5)


def test_sessao_primeiro_a_cinco():
    J1 = JogadorSala(IdJogador="a", NomeJogador="A", VitoriasRodada=5)
    assert SessaoAtingiuLimite(ModoVitorias, 3, 0, {"a": J1}, 5)


def test_placar_ordem_pontos():
    J1 = JogadorSala(IdJogador="a", NomeJogador="A", PontosAcumulados=10, VitoriasRodada=2)
    J2 = JogadorSala(IdJogador="b", NomeJogador="B", PontosAcumulados=15, VitoriasRodada=1)
    Placar = MontarPlacar({"a": J1, "b": J2}, ModoPontos)
    assert Placar[0]["idJogador"] == "b"


def test_placar_ordem_vitorias():
    J1 = JogadorSala(IdJogador="a", NomeJogador="A", PontosAcumulados=20, VitoriasRodada=2)
    J2 = JogadorSala(IdJogador="b", NomeJogador="B", PontosAcumulados=5, VitoriasRodada=4)
    Placar = MontarPlacar({"a": J1, "b": J2}, ModoVitorias)
    assert Placar[0]["idJogador"] == "b"


def test_vencedor_rodada_mesma_palavra():
    Config = ConfiguracaoSala(MesmaPalavra=True, ModoSessao=ModoVitorias)
    Sala = SalaJogo(CodigoSala="ABC123", CriadorId="a", Configuracao=Config)
    J1 = JogadorSala(IdJogador="a", NomeJogador="A", Venceu=True, Tentativas=[{"letras": []}])
    J2 = JogadorSala(
        IdJogador="b",
        NomeJogador="B",
        Venceu=True,
        Tentativas=[{"letras": []}, {"letras": []}],
    )
    Sala.Jogadores = {"a": J1, "b": J2}
    assert DeterminarVencedorRodada(Sala) == "a"


def test_contar_verdes():
    assert ContarVerdesTentativa({"estados": ["correto", "ausente", "correto"]}) == 2


def test_vencedores_por_verdes():
    J1 = JogadorSala(
        IdJogador="a",
        NomeJogador="A",
        Tentativas=[{"estados": ["correto", "ausente", "ausente", "ausente", "ausente"]}],
    )
    J2 = JogadorSala(
        IdJogador="b",
        NomeJogador="B",
        Tentativas=[{"estados": ["correto", "correto", "ausente", "ausente", "ausente"]}],
    )
    Vencedores, MaxV = DeterminarVencedoresRodadaPorVerdes([J1, J2])
    assert MaxV == 2
    assert Vencedores == ["b"]


def test_empate_verdes():
    J1 = JogadorSala(
        IdJogador="a",
        NomeJogador="A",
        Tentativas=[{"estados": ["correto", "correto", "ausente", "ausente", "ausente"]}],
    )
    J2 = JogadorSala(
        IdJogador="b",
        NomeJogador="B",
        Tentativas=[{"estados": ["correto", "correto", "presente", "ausente", "ausente"]}],
    )
    Vencedores, _ = DeterminarVencedoresRodadaPorVerdes([J1, J2])
    assert set(Vencedores) == {"a", "b"}


def test_rodada_encerra_mesma_palavra_sem_vencedor():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(MesmaPalavra=True)
    Sala = SalaJogo(
        CodigoSala="ABC123",
        CriadorId="a",
        Configuracao=Config,
        EstadoSala="jogando",
    )
    Sala.Jogadores = {
        "a": JogadorSala(IdJogador="a", NomeJogador="A", Finalizou=True),
        "b": JogadorSala(IdJogador="b", NomeJogador="B", Finalizou=True),
    }
    assert G.RodadaDeveEncerrar(Sala)


def test_rodada_encerra_mesma_palavra_com_vencedor():
    G = GerenciadorSalas()
    Config = ConfiguracaoSala(MesmaPalavra=True)
    Sala = SalaJogo(
        CodigoSala="ABC123",
        CriadorId="a",
        Configuracao=Config,
        EstadoSala="jogando",
    )
    Sala.Jogadores = {
        "a": JogadorSala(IdJogador="a", NomeJogador="A", Venceu=True, Finalizou=True),
        "b": JogadorSala(IdJogador="b", NomeJogador="B", Finalizou=False),
    }
    assert G.RodadaDeveEncerrar(Sala)


def test_sem_verdes_ninguem_vence():
    J1 = JogadorSala(IdJogador="a", NomeJogador="A", Tentativas=[{"estados": ["ausente"] * 5}])
    Vencedores, MaxV = DeterminarVencedoresRodadaPorVerdes([J1])
    assert Vencedores == []
    assert MaxV == 0
    assert MelhorContagemVerdes(J1) == 0


def test_mensagem_fim_rodada_mais_perto():
    J1 = JogadorSala(IdJogador="a", NomeJogador="Alpha")
    J2 = JogadorSala(IdJogador="b", NomeJogador="Beta")
    Historico = [
        {
            "rodada": 1,
            "porVerdes": True,
            "maxVerdes": 2,
            "vencedoresRodadaIds": ["b"],
            "resultados": [
                {"idJogador": "a", "verdesMelhor": 1},
                {"idJogador": "b", "verdesMelhor": 2},
            ],
        }
    ]
    MsgVencedor = MontarMensagemFimRodada(Historico, "b", {"a": J1, "b": J2})
    MsgPerdedor = MontarMensagemFimRodada(Historico, "a", {"a": J1, "b": J2})
    assert "mais perto" in MsgVencedor
    assert "2 verde" in MsgVencedor
    assert "Beta venceu" in MsgPerdedor
    assert "1 suas" in MsgPerdedor
