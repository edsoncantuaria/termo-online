import os
import sys
from pathlib import Path

import uvicorn

DiretorioSrc = Path(__file__).resolve().parent
if str(DiretorioSrc) not in sys.path:
    sys.path.insert(0, str(DiretorioSrc))

from servidor.aplicacao import CriarAplicacao  # noqa: E402

Aplicacao = CriarAplicacao()


def IniciarServidor() -> None:
    Porta = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "main:Aplicacao",
        host="0.0.0.0",
        port=Porta,
        reload=True,
        reload_dirs=[str(DiretorioSrc)],
    )


if __name__ == "__main__":
    IniciarServidor()
