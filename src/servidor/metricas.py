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
    from nucleo.controle_carga import MontarStatusCarga
    from nucleo.matchmaking import FilaGlobal
    from nucleo.redis_estado import StatusRedis
    from servidor.estado_global import GerenciadorVersus

    FilaGlobal.Processar(GerenciadorVersus)
    Salas = len(GerenciadorVersus.Salas)
    Fila = len(FilaGlobal.Fila)
    from nucleo.versao import InfoVersao

    return {
        **InfoVersao(),
        "uptimeSegundos": int(time.time() - InicioProcesso),
        "requisicoes": dict(Contadores),
        "salasAtivas": Salas,
        "filaRanqueada": Fila,
        "carga": MontarStatusCarga(SalasAtivas=Salas, FilaRanqueada=Fila),
        "redis": StatusRedis(),
    }


class MiddlewareMetricas(BaseHTTPMiddleware):
    async def dispatch(self, Requisicao: Request, Chamada):
        Caminho = Requisicao.url.path
        if Caminho.startswith("/api"):
            RegistrarMetrica(f"http:{Requisicao.method}:{Caminho.split('?')[0]}")
        return await Chamada(Requisicao)
