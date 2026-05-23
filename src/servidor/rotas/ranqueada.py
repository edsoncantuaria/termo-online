from fastapi import APIRouter, Depends

from nucleo.matchmaking import FilaGlobal
from nucleo.ranqueada import ListarElosApi
from nucleo.redis_estado import StatusRedis
from nucleo.temporada_ranqueada import MontarInfoTemporada
from servidor.dependencias_auth import ContaRegistrada
from servidor.estado_global import GerenciadorVersus
from servidor.websocket import BroadcastEstadoSala


def RegistrarRotasRanqueada(Roteador: APIRouter) -> None:
    @Roteador.get("/ranqueada/matchmaking")
    def InfoMatchmakingRanqueado():
        from nucleo.matchmaking_competitivo import (
            BUSCA_REAL_SEG,
            ESPERA_BOT_SEG,
            JANELA_RP_CRESCIMENTO_POR_SEG,
            JANELA_RP_INICIAL,
            JANELA_RP_MAXIMA,
            JANELA_RP_MESMO_ELO_EXTRA,
        )

        return {
            "janelaRpInicial": JANELA_RP_INICIAL,
            "crescimentoRpPorSegundo": JANELA_RP_CRESCIMENTO_POR_SEG,
            "janelaRpMaxima": JANELA_RP_MAXIMA,
            "bonusMesmoEloRp": JANELA_RP_MESMO_ELO_EXTRA,
            "buscaRealSegundos": BUSCA_REAL_SEG,
            "esperaOponenteSegundos": ESPERA_BOT_SEG,
            "descricao": (
                "Janela ±RP começa apertada e cresce na fila; "
                "pareia o oponente mais próximo dentro da janela."
            ),
        }

    @Roteador.get("/ranqueada/elos")
    def ListarElos():
        return {"elos": ListarElosApi()}

    @Roteador.get("/ranqueada/ranking")
    def RankingRanqueado(Perfil=Depends(ContaRegistrada)):
        from nucleo.ranking_ranqueado import MontarRankingCompleto

        return MontarRankingCompleto(Perfil)

    @Roteador.post("/ranqueada/revanche")
    async def RanqueadaRevanche(Perfil=Depends(ContaRegistrada)):
        FilaGlobal.Entrar(Perfil, GerenciadorVersus)
        R = FilaGlobal.SolicitarRevanche(Perfil["idConta"], GerenciadorVersus)
        Status = FilaGlobal.Status(Perfil["idConta"], GerenciadorVersus)
        if Status.get("estado") == "encontrado" and Status.get("codigoSala"):
            Sala = GerenciadorVersus.ObterSala(Status["codigoSala"])
            if Sala:
                await BroadcastEstadoSala(Sala)
        return {**R, "fila": Status}

    @Roteador.post("/ranqueada/fila")
    async def RanqueadaEntrarFila(Perfil=Depends(ContaRegistrada)):
        Status = FilaGlobal.Entrar(Perfil, GerenciadorVersus)
        if Status.get("estado") == "encontrado" and Status.get("codigoSala"):
            Sala = GerenciadorVersus.ObterSala(Status["codigoSala"])
            if Sala:
                await BroadcastEstadoSala(Sala)
        return Status

    @Roteador.delete("/ranqueada/fila")
    def RanqueadaSairFila(Perfil=Depends(ContaRegistrada)):
        FilaGlobal.Sair(Perfil["idConta"])
        return {"saiu": True}

    @Roteador.get("/ranqueada/fila")
    def RanqueadaStatusFila(Perfil=Depends(ContaRegistrada)):
        return FilaGlobal.Status(Perfil["idConta"], GerenciadorVersus)

    @Roteador.get("/ranqueada/temporada")
    def TemporadaRanqueada():
        return MontarInfoTemporada()

    @Roteador.get("/infra/redis")
    def InfraRedis():
        return StatusRedis()

    @Roteador.get("/infra/carga")
    def InfraCarga():
        from nucleo.controle_carga import MontarStatusCarga

        return MontarStatusCarga(
            SalasAtivas=len(GerenciadorVersus.Salas),
            FilaRanqueada=len(FilaGlobal.Fila),
        )
