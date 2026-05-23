from fastapi import APIRouter, Depends, HTTPException, Query

from nucleo.partida_sessao import DesistirPartida, RetomarPartida
from servidor.dependencias_auth import ContaOpcional
from servidor.estado_global import GerenciadorVersus
from servidor.rotas.schemas import DesistirPartidaRequest


def RegistrarRotasPartida(Roteador: APIRouter) -> None:
    @Roteador.get("/partida/{id_partida}/retomar")
    def RetomarPartidaHttp(
        id_partida: str,
        token: str | None = Query(default=None, alias="token"),
        id_jogador: str | None = Query(default=None, alias="id_jogador"),
        Perfil=Depends(ContaOpcional),
    ):
        IdConta = Perfil["idConta"] if Perfil else None
        Dados, Erro, Status = RetomarPartida(
            GerenciadorVersus,
            id_partida,
            token,
            id_jogador,
            IdConta,
        )
        if Erro:
            raise HTTPException(status_code=Status, detail=Erro)
        return Dados

    @Roteador.post("/partida/{id_partida}/desistir")
    async def DesistirPartidaHttp(id_partida: str, Corpo: DesistirPartidaRequest):
        from nucleo.partida_sessao import ObterSalaPorIdPartida

        SalaAntes = ObterSalaPorIdPartida(GerenciadorVersus, id_partida)
        Codigo = SalaAntes.CodigoSala if SalaAntes else None
        Dados, Erro, Status = DesistirPartida(
            GerenciadorVersus,
            id_partida,
            Corpo.idJogador,
            Corpo.tokenSessao,
        )
        if Erro:
            raise HTTPException(status_code=Status, detail=Erro)
        from servidor.websocket import BroadcastEstadoSala

        Codigo = Codigo or Dados.get("codigoSala")
        Sala = GerenciadorVersus.ObterSala(Codigo or "") if Codigo else None
        if Sala:
            await BroadcastEstadoSala(Sala)
        return Dados
