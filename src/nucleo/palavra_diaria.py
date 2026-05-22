import hashlib
from datetime import date

from .dicionario import ObterDicionario


def EscolherPalavraDoDia(DataReferencia: date | None = None) -> tuple[str, str, str]:
    """Mesma palavra para todos no mesmo dia (UTC-3 Brasil simplificado = local date)."""
    Data = DataReferencia or date.today()
    ChaveDia = Data.isoformat()
    PalavrasComAcento, PalavrasSemAcento, _ = ObterDicionario()
    Hash = int(hashlib.sha256(f"termo-{ChaveDia}".encode()).hexdigest(), 16)
    Indice = Hash % len(PalavrasSemAcento)
    return (
        PalavrasSemAcento[Indice],
        PalavrasComAcento[Indice],
        ChaveDia,
    )
