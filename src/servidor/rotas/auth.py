from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from nucleo.avatares import AVATARES
from nucleo.contas import (
    DefinirAvatarConta,
    EntrarComoVisitante,
    LoginConta,
    RegistrarConta,
)
from servidor.dependencias_auth import ContaOpcional, ContaRegistrada
from servidor.rotas.schemas import (
    AuthLoginRequest,
    AuthRegistroRequest,
    AuthVisitanteRequest,
)


class AvatarRequest(BaseModel):
    avatarId: str = Field(min_length=2, max_length=24)


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

    @Roteador.get("/auth/avatares")
    def ListarAvatares():
        return {"avatares": list(AVATARES)}

    @Roteador.patch("/auth/avatar")
    def AtualizarAvatar(Corpo: AvatarRequest, Perfil=Depends(ContaRegistrada)):
        try:
            Conta = DefinirAvatarConta(Perfil["idConta"], Corpo.avatarId)
        except ValueError as Erro:
            raise HTTPException(status_code=400, detail=str(Erro)) from Erro
        return {"conta": Conta}
