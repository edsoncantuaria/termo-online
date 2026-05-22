"""
Estado distribuído (opcional). Sem TERM0_REDIS_URL, tudo permanece em memória no processo.
Para múltiplas instâncias: configure Redis e evolua salas/fila para este módulo.
"""

import os
import logging

Log = logging.getLogger("termo.redis")

URL_REDIS = os.environ.get("TERM0_REDIS_URL", "").strip()


def RedisHabilitado() -> bool:
    return bool(URL_REDIS)


def StatusRedis() -> dict:
    if not RedisHabilitado():
        return {"habilitado": False, "modo": "memoria"}
    return {
        "habilitado": True,
        "modo": "redis_configurado",
        "nota": "Estado de salas/fila ainda em memória; migração planejada.",
    }
