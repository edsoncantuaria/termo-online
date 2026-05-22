import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.gerenciador_salas import ConfiguracaoSala, GerenciadorSalas
from nucleo.logica_jogo import ValidarPalavra
from servidor.websocket import ProcessarChuteSala


def _SalaEmJogo():
    Gerenciador = GerenciadorSalas()
    Config = ConfiguracaoSala(MaximoJogadores=2, MesmaPalavra=True)
    Sala, Host = Gerenciador.CriarSala("Host", Config)
    _, Convidado, Erro = Gerenciador.EntrarSala(Sala.CodigoSala, "Convidado")
    assert Erro is None
    Host.Pronto = True
    Convidado.Pronto = True
    assert Gerenciador.IniciarPartida(Sala, Host.IdJogador) is None
    assert Sala.EstadoSala == "jogando"
    return Gerenciador, Sala, Host


def test_chute_invalido_nao_grava_tentativa_no_jogador():
    """Servidor rejeita palavra inválida sem alterar o histórico (contrato para a UI)."""
    _, Sala, Host = _SalaEmJogo()
    Antes = len(Host.Tentativas)

    Valido, Mensagem = ValidarPalavra("xxxxx", Host.Tentativas)
    assert Valido is False
    assert Mensagem

    assert len(Host.Tentativas) == Antes


def test_processar_chute_invalido_responde_chute_invalido():
    _, Sala, Host = _SalaEmJogo()
    Antes = len(Host.Tentativas)
    Enviadas: list[dict] = []

    async def Capturar(_codigo, _id_jogador, Mensagem):
        Enviadas.append(Mensagem)

    with (
        patch("servidor.websocket.EnviarParaJogador", Capturar),
        patch("servidor.websocket.BroadcastEstadoSala", new_callable=AsyncMock),
    ):
        asyncio.run(ProcessarChuteSala(Sala, Host.IdJogador, "xxxxx"))

    assert len(Host.Tentativas) == Antes
    assert Enviadas[-1]["tipo"] == "chuteInvalido"
    assert "dicionário" in Enviadas[-1]["mensagem"].lower()
