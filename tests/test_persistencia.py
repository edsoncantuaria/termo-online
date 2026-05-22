import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia


def test_diaria_unica_por_nick(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "test.db")
    persistencia.InicializarBanco()
    persistencia.RegistrarDiaria("Jogador1", "2026-05-21", True, 3, 500, "grid")
    assert persistencia.JaJogouDiaria("Jogador1", "2026-05-21") is True
    assert persistencia.JaJogouDiaria("Outro", "2026-05-21") is False
