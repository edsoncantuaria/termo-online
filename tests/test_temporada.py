import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.temporada_ranqueada import IdTemporadaAtual, MontarInfoTemporada


def test_id_temporada():
    assert IdTemporadaAtual(date(2026, 5, 21)) == "2026-05"


def test_info_temporada():
    Info = MontarInfoTemporada()
    assert "id" in Info
    assert "proximoReset" in Info
