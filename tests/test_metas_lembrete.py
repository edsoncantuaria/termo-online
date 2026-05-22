import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo import persistencia
from nucleo.metas_semanais import LembreteMetasPendentes, RegistrarProgressoMeta


def test_lembrete_metas(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "meta.db")
    persistencia.InicializarBanco()
    Id = persistencia.CriarConta("meta_user", "hash", "salt", Email="m@e.com")
    RegistrarProgressoMeta(Id, "arena_rodada", 3)
    Texto = LembreteMetasPendentes(Id)
    assert Texto and "arena" in Texto.lower()
