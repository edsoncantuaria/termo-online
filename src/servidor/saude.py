"""Endpoints de saúde e prontidão."""

from fastapi import APIRouter

from nucleo import persistencia
from nucleo.dicionario import ObterDicionario

RoteadorSaude = APIRouter(tags=["saude"])


@RoteadorSaude.get("/api/health")
def Health():
    _, Palavras, _ = ObterDicionario()
    return {
        "status": "ok",
        "servico": "termo-online",
        "dicionarioCarregado": len(Palavras) > 0,
        "palavrasNoDicionario": len(Palavras),
    }


@RoteadorSaude.get("/api/ready")
def Ready():
    try:
        persistencia.InicializarBanco()
        with persistencia.Conexao() as C:
            C.execute("SELECT 1").fetchone()
        return {"pronto": True, "banco": "ok"}
    except Exception as Erro:
        return {"pronto": False, "banco": "erro", "detalhe": str(Erro)}
