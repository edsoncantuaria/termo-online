from fastapi import APIRouter

from servidor.rotas.arena import RegistrarRotasArena
from servidor.rotas.auth import RegistrarRotasAuth
from servidor.rotas.jogo import RegistrarRotasJogo
from servidor.rotas.misc import RegistrarRotasMisc
from servidor.rotas.partida import RegistrarRotasPartida
from servidor.rotas.ranqueada import RegistrarRotasRanqueada


def RegistrarRotas(Aplicacao) -> None:
    Roteador = APIRouter(prefix="/api")
    RegistrarRotasMisc(Roteador)
    RegistrarRotasAuth(Roteador)
    RegistrarRotasRanqueada(Roteador)
    RegistrarRotasJogo(Roteador)
    RegistrarRotasPartida(Roteador)
    RegistrarRotasArena(Roteador)
    Aplicacao.include_router(Roteador)
