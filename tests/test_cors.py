"""CORS na API (inclui respostas de middleware)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient

from servidor.aplicacao import CriarAplicacao

ORIGEM = "https://termo.cloudive.com.br"


def test_cors_preflight_api():
    Cliente = TestClient(CriarAplicacao())
    R = Cliente.options(
        "/api/salas/publicas",
        headers={
            "Origin": ORIGEM,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert R.status_code == 200
    assert R.headers.get("access-control-allow-origin") == ORIGEM


def test_cors_get_com_origin():
    Cliente = TestClient(CriarAplicacao())
    R = Cliente.get("/api/salas/publicas", headers={"Origin": ORIGEM})
    assert R.headers.get("access-control-allow-origin") == ORIGEM
