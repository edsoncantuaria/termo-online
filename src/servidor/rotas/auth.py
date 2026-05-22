from fastapi import APIRouter, Depends, HTTPException

from nucleo.contas import (
    EntrarComoVisitante,
    LoginConta,
    RegistrarConta,
)
from servidor.dependencias_auth import ContaOpcional
from servidor.rotas.schemas import (
    AuthLoginRequest,
    AuthRegistroRequest,
    AuthVisitanteRequest,
)


def RegistrarRotasAuth(Roteador: APIRouter) -> None:
    @Roteador.post("/auth/registrar")
    def AuthRegistrar(Corpo: AuthRegistroRequest):
        try:
            Perfil, Token = RegistrarConta(Corpo.nick, Corpo.email, Corpo.senha)
        except ValueError as Erro:
            raise HTTPException(status_code=400, detail=str(Erro)) from Erro
        return {"conta": Perfil, "token": Token}

    @Roteador.post("/auth/login")
    def AuthLogin(Corpo: AuthLoginRequest):
        try:
            Perfil, Token = LoginConta(Corpo.identificador, Corpo.senha)
        except ValueError as Erro:
            raise HTTPException(status_code=401, detail=str(Erro)) from Erro
        return {"conta": Perfil, "token": Token}

    @Roteador.post("/auth/visitante")
    def AuthVisitante(Corpo: AuthVisitanteRequest = AuthVisitanteRequest()):
        try:
            Perfil, Token = EntrarComoVisitante(Corpo.nick)
        except ValueError as Erro:
            raise HTTPException(status_code=400, detail=str(Erro)) from Erro
        return {"conta": Perfil, "token": Token}

    @Roteador.get("/auth/eu")
    def AuthEu(Perfil=Depends(ContaOpcional)):
        if not Perfil:
            raise HTTPException(status_code=401, detail="Não autenticado.")
        return {"conta": Perfil}
