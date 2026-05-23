"""
Estado distribuído (opcional). Sem TERM0_REDIS_URL, rate limit e fila ficam em memória.
Com Redis: rate limit, fila ranqueada e roteamento de salas entre workers.
"""

from __future__ import annotations

import logging
import os
import socket
import time
from collections import defaultdict

Log = logging.getLogger("termo.redis")

URL_REDIS = os.environ.get("TERM0_REDIS_URL", "").strip()
_ClienteRedis = None
_ContadoresMemoria: dict[str, list[float]] = defaultdict(list)
_IdWorker = os.environ.get("TERM0_WORKER_ID", "").strip()
_TTL_SALA_WORKER_SEG = 7200


def RedisHabilitado() -> bool:
    return bool(URL_REDIS)


def _ObterCliente():
    global _ClienteRedis
    if _ClienteRedis is not None:
        return _ClienteRedis
    if not URL_REDIS:
        return None
    try:
        import redis

        _ClienteRedis = redis.Redis.from_url(URL_REDIS, decode_responses=True)
        _ClienteRedis.ping()
        return _ClienteRedis
    except Exception as Erro:
        Log.warning("Redis indisponível (%s); usando memória.", Erro)
        return None


def IdWorker() -> str:
    global _IdWorker
    if not _IdWorker:
        Host = socket.gethostname().split(".")[0][:24]
        _IdWorker = f"{Host}-{os.getpid()}"
    return _IdWorker


def AdquirirLockRedis(Chave: str, Segundos: int = 3) -> bool:
    Cliente = _ObterCliente()
    if not Cliente:
        return True
    try:
        return bool(Cliente.set(Chave, IdWorker(), nx=True, ex=Segundos))
    except Exception as Erro:
        Log.warning("Lock Redis falhou (%s): %s", Chave, Erro)
        return True


def RegistrarSalaNoWorker(CodigoSala: str) -> None:
    Cliente = _ObterCliente()
    if not Cliente or not CodigoSala:
        return
    try:
        Chave = f"termo:sala:{CodigoSala.upper()}:worker"
        Cliente.set(Chave, IdWorker(), ex=_TTL_SALA_WORKER_SEG)
    except Exception as Erro:
        Log.warning("Registrar sala no worker falhou: %s", Erro)


def WorkerDaSala(CodigoSala: str) -> str | None:
    Cliente = _ObterCliente()
    if not Cliente or not CodigoSala:
        return None
    try:
        return Cliente.get(f"termo:sala:{CodigoSala.upper()}:worker")
    except Exception:
        return None


def VerificarWorkerDonoSala(CodigoSala: str) -> tuple[bool, str | None]:
    """True se esta instância pode atender a sala (memória local ou dono no Redis)."""
    if not RedisHabilitado() or not _ObterCliente():
        return True, None
    Dono = WorkerDaSala(CodigoSala)
    if not Dono:
        return True, None
    Eu = IdWorker()
    if Dono == Eu:
        return True, Dono
    return False, Dono


def StatusRedis() -> dict:
    from .redis_fila import FilaRedisDisponivel

    if not RedisHabilitado():
        return {
            "habilitado": False,
            "modo": "memoria",
            "workerId": IdWorker(),
        }
    Cliente = _ObterCliente()
    if Cliente:
        return {
            "habilitado": True,
            "modo": "redis_ativo",
            "workerId": IdWorker(),
            "filaRedis": FilaRedisDisponivel(),
            "nota": (
                "Rate limit e fila ranqueada compartilhados; "
                "salas no processo — prefira uma API por VM (tunnel direto)."
            ),
        }
    return {
        "habilitado": True,
        "modo": "redis_falhou",
        "workerId": IdWorker(),
        "nota": "URL configurada mas conexão falhou; fallback em memória.",
    }


def PermitirRequisicaoRateLimit(Chave: str, Limite: int, JanelaSegundos: int = 60) -> bool:
    """True se a requisição pode seguir (contagem < limite na janela)."""
    Cliente = _ObterCliente()
    if Cliente:
        try:
            ChaveRedis = f"termo:rl:{Chave}"
            Pipeline = Cliente.pipeline()
            Pipeline.incr(ChaveRedis)
            Pipeline.expire(ChaveRedis, JanelaSegundos)
            Contagem, _ = Pipeline.execute()
            return int(Contagem) <= Limite
        except Exception as Erro:
            Log.warning("Rate limit Redis falhou: %s", Erro)

    Agora = time.time()
    Historico = _ContadoresMemoria[Chave]
    Historico[:] = [T for T in Historico if Agora - T < JanelaSegundos]
    if len(Historico) >= Limite:
        return False
    Historico.append(Agora)
    return True
