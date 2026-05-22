import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from nucleo.dicionario import CarregarDicionario

from .manutencao import TarefaManutencaoSalas
from .rate_limit import MiddlewareRateLimit
from .rotas import RegistrarRotas
from .websocket import RegistrarWebSocket


@asynccontextmanager
async def CicloVida(Aplicacao: FastAPI):
    Tarefa = asyncio.create_task(TarefaManutencaoSalas())
    yield
    Tarefa.cancel()
    try:
        await Tarefa
    except asyncio.CancelledError:
        pass


def CriarAplicacao() -> FastAPI:
    CarregarDicionario()

    Aplicacao = FastAPI(
        title="Termo Online",
        description="Jogo de palavras em português com pontuação e modo Arena",
        version="3.0.0",
        lifespan=CicloVida,
    )

    Aplicacao.add_middleware(MiddlewareRateLimit)
    RegistrarRotas(Aplicacao)
    RegistrarWebSocket(Aplicacao)  # registra também notificador do lobby

    CaminhoEstatico = Path(__file__).resolve().parent.parent / "static"
    CaminhoDist = CaminhoEstatico / "dist"

    if (CaminhoDist / "index.html").exists():

        @Aplicacao.get("/")
        async def PaginaInicial():
            return FileResponse(CaminhoDist / "index.html")

        Aplicacao.mount(
            "/assets",
            StaticFiles(directory=CaminhoDist / "assets"),
            name="assets",
        )

        @Aplicacao.get("/{caminho:path}")
        async def SpaFallback(caminho: str):
            if caminho.startswith("api/") or caminho.startswith("ws/"):
                raise HTTPException(status_code=404)
            Arquivo = CaminhoDist / caminho
            if Arquivo.is_file():
                return FileResponse(Arquivo)
            return FileResponse(CaminhoDist / "index.html")
    else:

        @Aplicacao.get("/")
        async def FrontendNaoConstruido():
            return HTMLResponse(
                """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Termo — build pendente</title>
<style>body{font-family:system-ui,sans-serif;max-width:32rem;margin:3rem auto;padding:0 1rem}
code{background:#eee;padding:.15rem .4rem;border-radius:4px}</style></head>
<body>
<h1>Frontend Vue não construído</h1>
<p>Na raiz do projeto:</p>
<pre><code>make install
make run</code></pre>
<p>Desenvolvimento com hot-reload (UI na porta 5173):</p>
<pre><code>make dev</code></pre>
</body></html>""",
                status_code=503,
            )

        @Aplicacao.get("/{caminho:path}")
        async def FrontendNaoConstruidoFallback(caminho: str):
            if caminho.startswith("api/") or caminho.startswith("ws/"):
                raise HTTPException(status_code=404)
            return await FrontendNaoConstruido()

    return Aplicacao
