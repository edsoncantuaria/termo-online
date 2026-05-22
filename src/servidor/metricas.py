"""Métricas simples em memória (por processo)."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

InicioProcesso = time.time()
Contadores: dict[str, int] = defaultdict(int)


def RegistrarMetrica(Nome: str, Valor: int = 1) -> None:
    Contadores[Nome] += Valor


def MontarSnapshotMetricas() -> dict:
    from servidor.estado_global import GerenciadorVersus
    from nucleo.matchmaking import FilaGlobal

    FilaGlobal.Processar(GerenciadorVersus)
    return {
        "uptimeSegundos": int(time.time() - InicioProcesso),
        "requisicoes": dict(Contadores),
        "salasAtivas": len(GerenciadorVersus.Salas),
        "filaRanqueada": len(FilaGlobal.Fila),
    }


class MiddlewareMetricas(BaseHTTPMiddleware):
    async def dispatch(self, Requisicao: Request, Chamada):
        Caminho = Requisicao.url.path
        if Caminho.startswith("/api"):
            RegistrarMetrica(f"http:{Requisicao.method}:{Caminho.split('?')[0]}")
        return await Chamada(Requisicao)
