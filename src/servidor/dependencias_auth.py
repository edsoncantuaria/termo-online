from typing import Annotated

from fastapi import Depends, Header, HTTPException

from nucleo.contas import InstanciaContaValida, ResolverSessao


def ObterToken(
    authorization: Annotated[str | None, Header()] = None,
    x_termo_token: Annotated[str | None, Header()] = None,
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return x_termo_token


def ContaOpcional(
    Token: Annotated[str | None, Depends(ObterToken)],
    Instancia: Annotated[str | None, Header(alias="X-Termo-Instancia")] = None,
):
    Perfil = ResolverSessao(Token)
    if Perfil and not InstanciaContaValida(Perfil["idConta"], Instancia):
        raise HTTPException(
            status_code=409,
            detail="Esta conta foi aberta em outro dispositivo ou aba. Entre novamente.",
        )
    return Perfil


def ContaObrigatoria(Perfil=Depends(ContaOpcional)):
    if not Perfil:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    return Perfil


def ContaRegistrada(Perfil=Depends(ContaObrigatoria)):
    if Perfil.get("ehVisitante"):
        raise HTTPException(
            status_code=403,
            detail="Crie uma conta para acessar ranking e modo ranqueado.",
        )
    return Perfil
