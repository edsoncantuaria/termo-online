import hashlib
from datetime import date

from .dicionario import ObterDicionario
from .tempo_brasil import DataHojeBrasil


def EscolherPalavraDoDia(DataReferencia: date | None = None) -> tuple[str, str, str]:
    """Mesma palavra para todos no mesmo dia (calendário America/Sao_Paulo, UTC-3)."""
    Data = DataReferencia or DataHojeBrasil()
    ChaveDia = Data.isoformat()
    PalavrasComAcento, PalavrasSemAcento, _ = ObterDicionario()
    Hash = int(hashlib.sha256(f"termo-{ChaveDia}".encode()).hexdigest(), 16)
    Indice = Hash % len(PalavrasSemAcento)
    return (
        PalavrasSemAcento[Indice],
        PalavrasComAcento[Indice],
        ChaveDia,
    )
