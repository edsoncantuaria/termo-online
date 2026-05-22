import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.matchmaking_competitivo import PARTIDAS_PLACEMENT, PodeParearRp


def test_placement_amplia_janela():
    assert not PodeParearRp(500, 0, 900, 0, PartidasA=99, PartidasB=99)
    assert not PodeParearRp(500, 0, 680, 0, PartidasA=99, PartidasB=99)
    assert PodeParearRp(500, 0, 680, 0, PartidasA=2, PartidasB=99)
    assert PARTIDAS_PLACEMENT == 5
