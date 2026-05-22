"""Limite simples de requisições por IP (anti-spam)."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

JanelaSegundos = 60
MaximoPorJanela = 120
Contadores: dict[str, list[float]] = defaultdict(list)


def _IpCliente(Requisicao: Request) -> str:
    Encaminhado = Requisicao.headers.get("x-forwarded-for")
    if Encaminhado:
        return Encaminhado.split(",")[0].strip()
    if Requisicao.client:
        return Requisicao.client.host
    return "local"


class MiddlewareRateLimit(BaseHTTPMiddleware):
    async def dispatch(self, Requisicao: Request, Chamada):
        Caminho = Requisicao.url.path
        if not Caminho.startswith("/api"):
            return await Chamada(Requisicao)

        Ip = _IpCliente(Requisicao)
        Agora = time.time()
        Historico = Contadores[Ip]
        Historico[:] = [T for T in Historico if Agora - T < JanelaSegundos]
        if len(Historico) >= MaximoPorJanela:
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisições. Aguarde um momento."},
            )
        Historico.append(Agora)
        return await Chamada(Requisicao)
