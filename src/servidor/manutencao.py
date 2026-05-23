import asyncio

from nucleo.bot_jogador import ProcessarBotsNasSalas
from nucleo.matchmaking import FilaGlobal
from nucleo.partida_sessao import VerificarPausasExpiradas
from servidor.estado_global import GerenciadorVersus as Gerenciador
from servidor.websocket import BroadcastEstadoSala, VerificarFimRodada


async def TarefaManutencaoSalas() -> None:
    while True:
        await asyncio.sleep(2)
        FilaGlobal.Processar(Gerenciador)
        for Sala in VerificarPausasExpiradas(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in ProcessarBotsNasSalas(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in list(Gerenciador.Salas.values()):
            if Sala.PartidaEncerrada:
                continue

            Mudou = False
            if Gerenciador.LimparJogadoresInativos(Sala):
                Mudou = True

            if Sala.EstadoSala == "countdown":
                if Gerenciador.PromoverCountdown(Sala):
                    Mudou = True

            if Sala.EstadoSala == "jogando":
                if Gerenciador.VerificarTempoEsgotado(Sala):
                    VerificarFimRodada(Sala)
                    Mudou = True

            if Mudou and Gerenciador.ObterSala(Sala.CodigoSala):
                await BroadcastEstadoSala(Sala)
