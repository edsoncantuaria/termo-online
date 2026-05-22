"""Configuração mínima de logging estruturado."""

import logging
import os
import sys


def ConfigurarLogging() -> None:
    Nivel = os.environ.get("TERM0_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, Nivel, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
