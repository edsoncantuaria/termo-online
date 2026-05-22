import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient

from servidor.aplicacao import CriarAplicacao


def test_health_e_ready():
    Cliente = TestClient(CriarAplicacao())
    H = Cliente.get("/api/health")
    assert H.status_code == 200
    assert H.json()["status"] == "ok"
    R = Cliente.get("/api/ready")
    assert R.status_code == 200
    assert R.json()["pronto"] is True
