"""Respostas 503/429 quando o servidor está no limite de carga."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from nucleo.controle_carga import MontarStatusCarga, PodeCriarSala
from nucleo.redis_estado import VerificarWorkerDonoSala
from servidor.estado_global import GerenciadorVersus


def _CodigoSalaDoCaminho(Caminho: str) -> str | None:
    Partes = Caminho.strip("/").split("/")
    if len(Partes) >= 3 and Partes[0] == "api" and Partes[1] == "sala":
        return Partes[2].upper()
    return None


class MiddlewareControleCarga(BaseHTTPMiddleware):
    async def dispatch(self, Requisicao: Request, Chamada):
        Caminho = Requisicao.url.path

        if Caminho == "/api/sala/criar" and Requisicao.method == "POST":
            Admissao = PodeCriarSala(len(GerenciadorVersus.Salas))
            if not Admissao.Permitido:
                return JSONResponse(
                    status_code=503,
                    content={"detail": Admissao.Mensagem},
                    headers={
                        "Retry-After": str(Admissao.RetryAfterSegundos),
                    },
                )

        Codigo = _CodigoSalaDoCaminho(Caminho)
        if Codigo and Caminho.startswith("/api/sala/"):
            DonoOk, WorkerRemoto = VerificarWorkerDonoSala(Codigo)
            if not DonoOk:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": (
                            "Esta sala está em outro processo da API. "
                            "Use uma única instância termo-api (recomendado) ou um origin fixo no tunnel."
                        ),
                        "workerId": WorkerRemoto,
                    },
                    headers={"X-Termo-Worker": WorkerRemoto or ""},
                )

        return await Chamada(Requisicao)
