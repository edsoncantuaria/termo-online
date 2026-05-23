import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.gerenciador_salas import (
    ConfiguracaoSala,
    GerenciadorSalas,
    TempoInativoArenaLobbySegundos,
)


def test_expulsa_jogador_inativo_no_lobby_arena():
    Gerenciador = GerenciadorSalas()
    Config = ConfiguracaoSala(MaximoJogadores=4)
    Sala, Host = Gerenciador.CriarSala("Host", Config)
    assert Sala.EstadoSala == "aguardando"

    Host.UltimaAtividade = time.time() - TempoInativoArenaLobbySegundos - 1
    Host.Conectado = True

    Mudou, Expulsos = Gerenciador.LimparJogadoresInativos(Sala)
    assert Mudou
    assert Expulsos == [(Host.IdJogador, "inatividade")]
    assert Host.IdJogador not in Sala.Jogadores


def test_espectador_ve_tentativas_de_todos():
    Gerenciador = GerenciadorSalas()
    Config = ConfiguracaoSala(MaximoJogadores=2, VerOutros=False, MesmaPalavra=True)
    Sala, Host = Gerenciador.CriarSala("Host", Config)
    _, Convidado, _ = Gerenciador.EntrarSala(Sala.CodigoSala, "Convidado")
    Host.Pronto = True
    Convidado.Pronto = True
    Gerenciador.IniciarPartida(Sala, Host.IdJogador)
    _, Espectador, Erro = Gerenciador.EntrarSala(
        Sala.CodigoSala, "Espectador", Espectador=True
    )
    assert Erro is None
    Gerenciador.AplicarChuteJogador(Sala, Host.IdJogador, Host.PalavraSecreta or "AAAAA")

    Estado = Gerenciador.EstadoPublicoSala(Sala, Espectador.IdJogador)
    HostSerializado = next(
        J for J in Estado["jogadores"] if J["nomeJogador"] == "Host"
    )
    assert len(HostSerializado["tentativas"]) >= 1
