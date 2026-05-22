"""Limite de requisições por IP (anti-spam), com tetos por rota sensível."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

JanelaSegundos = 60
MaximoPorJanela = 120
Contadores: dict[str, list[float]] = defaultdict(list)

LimitesPorPrefixo: list[tuple[str, int]] = [
    ("/api/auth/registrar", 8),
    ("/api/auth/login", 15),
    ("/api/auth/visitante", 20),
    ("/api/jogar/chute", 90),
    ("/api/solo/chute", 90),
]


def _IpCliente(Requisicao: Request) -> str:
    Encaminhado = Requisicao.headers.get("x-forwarded-for")
    if Encaminhado:
        return Encaminhado.split(",")[0].strip()
    if Requisicao.client:
        return Requisicao.client.host
    return "local"


def _LimiteParaCaminho(Caminho: str) -> int:
    for Prefixo, Limite in LimitesPorPrefixo:
        if Caminho.startswith(Prefixo):
            return Limite
    return MaximoPorJanela


class MiddlewareRateLimit(BaseHTTPMiddleware):
    async def dispatch(self, Requisicao: Request, Chamada):
        Caminho = Requisicao.url.path
        if not Caminho.startswith("/api"):
            return await Chamada(Requisicao)

        Ip = _IpCliente(Requisicao)
        Chave = f"{Ip}:{Caminho.split('?')[0]}"
        Agora = time.time()
        Historico = Contadores[Chave]
        Historico[:] = [T for T in Historico if Agora - T < JanelaSegundos]
        Limite = _LimiteParaCaminho(Caminho)
        if len(Historico) >= Limite:
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisições. Aguarde um momento."},
            )
        Historico.append(Agora)
        return await Chamada(Requisicao)
