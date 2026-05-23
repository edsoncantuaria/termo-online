import asyncio
import time

from nucleo import persistencia
from nucleo.bot_jogador import ProcessarBotsNasSalas
from nucleo.matchmaking import FilaGlobal
from nucleo.partida_sessao import (
    ProcessarSalasComJogadoresOffline,
    VerificarAbandonosProlongados,
    VerificarPausasExpiradas,
)
from servidor.estado_global import GerenciadorVersus as Gerenciador
from servidor.websocket import (
    BroadcastEstadoSala,
    EnviarParaJogador,
    VerificarFimRodada,
)

_UltimaLimpezaSnapshots = 0.0


async def TarefaManutencaoSalas() -> None:
    global _UltimaLimpezaSnapshots
    while True:
        await asyncio.sleep(2)
        Agora = time.time()
        if Agora - _UltimaLimpezaSnapshots >= 600:
            persistencia.LimparSnapshotsEncerradosAntigos(48)
            _UltimaLimpezaSnapshots = Agora
        FilaGlobal.Processar(Gerenciador)
        for Sala in ProcessarSalasComJogadoresOffline(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in VerificarPausasExpiradas(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in VerificarAbandonosProlongados(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in ProcessarBotsNasSalas(Gerenciador):
            VerificarFimRodada(Sala)
            await BroadcastEstadoSala(Sala)
        for Sala in list(Gerenciador.Salas.values()):
            if Sala.PartidaEncerrada:
                continue

            Mudou = False
            MudouInativos, Expulsos = Gerenciador.LimparJogadoresInativos(Sala)
            if MudouInativos:
                Mudou = True
                for IdJogador, Motivo in Expulsos:
                    if Motivo == "inatividade":
                        Texto = (
                            "Você foi expulso da arena por inatividade "
                            "(2 minutos sem interação na sala de espera)."
                        )
                    else:
                        Texto = "Você foi removido da sala por desconexão prolongada."
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        IdJogador,
                        {"tipo": "expulso", "mensagem": Texto},
                    )

            if Sala.EstadoSala == "countdown":
                if Gerenciador.PromoverCountdown(Sala):
                    Mudou = True

            if Sala.EstadoSala == "jogando":
                if Gerenciador.FinalizarAusentesRodadaAtual(Sala):
                    VerificarFimRodada(Sala)
                    Mudou = True
                if Gerenciador.VerificarTempoEsgotado(Sala):
                    VerificarFimRodada(Sala)
                    Mudou = True

            if Mudou and Gerenciador.ObterSala(Sala.CodigoSala):
                await BroadcastEstadoSala(Sala)
