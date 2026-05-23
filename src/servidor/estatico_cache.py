"""Cabeçalhos HTTP para o build Vue — evita HTML/SW presos em cache."""

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

CABECALHOS_SEM_CACHE = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
}

CABECALHOS_ASSET_HASH = {
    "Cache-Control": "public, max-age=31536000, immutable",
}

NOMES_SEM_CACHE = frozenset(
    {
        "index.html",
        "sw.js",
        "registerSW.js",
        "manifest.webmanifest",
        "workbox-sw.js",
    }
)


def _NomeArquivo(Caminho: Path) -> str:
    return Caminho.name.lower()


def EhAssetComHash(Caminho: Path) -> bool:
    """JS/CSS em /assets/ com hash no nome (Vite)."""
    if "assets" not in Caminho.parts:
        return False
    Nome = _NomeArquivo(Caminho)
    return Nome.endswith((".js", ".css", ".woff2"))


def EhArquivoSemCache(Caminho: Path) -> bool:
    Nome = _NomeArquivo(Caminho)
    if Nome in NOMES_SEM_CACHE:
        return True
    if Nome.startswith("workbox-") and Nome.endswith(".js"):
        return True
    return False


def RespostaArquivoDist(Arquivo: Path) -> FileResponse:
    if not Arquivo.is_file():
        raise HTTPException(status_code=404)
    if EhAssetComHash(Arquivo):
        return FileResponse(Arquivo, headers=CABECALHOS_ASSET_HASH)
    if EhArquivoSemCache(Arquivo):
        return FileResponse(Arquivo, headers=CABECALHOS_SEM_CACHE)
    return FileResponse(Arquivo, headers=CABECALHOS_SEM_CACHE)
