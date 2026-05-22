"""
Estado distribuído (opcional). Sem TERM0_REDIS_URL, rate limit e demais usos ficam em memória.
Com Redis: rate limit compartilhado entre workers (salas/fila ainda no processo).
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict

Log = logging.getLogger("termo.redis")

URL_REDIS = os.environ.get("TERM0_REDIS_URL", "").strip()
_ClienteRedis = None
_ContadoresMemoria: dict[str, list[float]] = defaultdict(list)


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


def StatusRedis() -> dict:
    if not RedisHabilitado():
        return {"habilitado": False, "modo": "memoria"}
    Cliente = _ObterCliente()
    if Cliente:
        return {
            "habilitado": True,
            "modo": "redis_ativo",
            "nota": "Rate limit compartilhado; salas/fila ainda em memória por processo.",
        }
    return {
        "habilitado": True,
        "modo": "redis_falhou",
        "nota": "URL configurada mas conexão falhou; rate limit em memória.",
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
