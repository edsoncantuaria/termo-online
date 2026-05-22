import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.bot_jogador import _FiltrarPorFeedback
from nucleo.logica_jogo import AvaliarChute


def test_filtrar_por_feedback_respeita_verdes():
    Estados = [E.value for E in AvaliarChute("termo", "terno")]
    Tentativas = [{"letras": list("TERNO"), "estados": Estados}]
    Candidatos = ["termo", "tordo", "terna", "torre"]
    Filtradas = _FiltrarPorFeedback(Candidatos, Tentativas)
    assert Filtradas == ["termo"]
