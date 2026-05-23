"""Contas, sessões e autenticação (sem confiar no frontend para pontos)."""

import hashlib
import hmac
import random
import re
import secrets
from datetime import datetime, timedelta, timezone

from . import persistencia
from .avatares import AvatarValido, ResolverAvatarId
from .ranqueada import EloDePontos, NomeEloExibicao, PONTOS_INICIAIS

ITERACOES_SENHA = 120_000
DURACAO_SESSAO_DIAS = 30
NICK_RE = re.compile(r"^[a-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")

NOMES_BASE_VISITANTE = (
    "maria",
    "joao",
    "ana",
    "pedro",
    "lucas",
    "julia",
    "rafa",
    "laura",
    "bruno",
    "helena",
    "carlos",
    "sofia",
    "diego",
    "camila",
    "gabi",
    "theo",
)


def _AgoraUtc() -> datetime:
    return datetime.now(timezone.utc)


def _HashSenha(Senha: str, Salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        Senha.encode("utf-8"),
        Salt.encode("utf-8"),
        ITERACOES_SENHA,
    ).hex()


def ValidarNick(Nick: str) -> str:
    N = Nick.strip().lower()[:20]
    if not NICK_RE.match(N):
        raise ValueError(
            "Nick inválido: use 3–20 caracteres (letras minúsculas, números ou _)."
        )
    return N


def ValidarEmail(Email: str) -> str:
    E = Email.strip().lower()[:120]
    if not EMAIL_RE.match(E):
        raise ValueError("Informe um e-mail válido.")
    return E


def ValidarSenha(Senha: str) -> None:
    if len(Senha) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")


def _NickOcupado(Nick: str) -> bool:
    Conta = persistencia.ObterContaPorNick(Nick)
    if not Conta:
        return False
    if Conta.get("eh_visitante") and persistencia.VisitanteEstaInativo(Conta):
        return False
    return True


def _RemoverVisitanteInativoNoNick(Nick: str) -> None:
    Conta = persistencia.ObterContaPorNick(Nick)
    if not Conta or not Conta.get("eh_visitante"):
        return
    if not persistencia.VisitanteEstaInativo(Conta):
        return
    persistencia.ExcluirConta(Conta["id"])


def _ProximoNickLivre(Prefixo: str, *, Ignorar: str | None = None) -> str:
    if Prefixo != Ignorar and not _NickOcupado(Prefixo):
        return Prefixo
    for I in range(1, 10_000):
        Candidato = f"{Prefixo}{I}"
        if Candidato == Ignorar:
            continue
        if len(Candidato) > 20:
            break
        if not _NickOcupado(Candidato):
            return Candidato
    Sufixo = secrets.token_hex(2)
    return _ProximoNickLivre(f"jogador{Sufixo}")


def GerarNickVisitante() -> str:
    Base = random.choice(NOMES_BASE_VISITANTE)
    return _ProximoNickLivre(Base)


def ReservarNickVisitante(NickPreferido: str | None = None) -> str:
    if not NickPreferido or not str(NickPreferido).strip():
        return GerarNickVisitante()
    return _ProximoNickLivre(ValidarNick(NickPreferido))


def _DeslocarNickVisitante(NickAtual: str) -> str:
    """Quem cria conta fica com o nick; visitante ganha sufixo (ex.: maria1 → maria10)."""
    Candidato = f"{NickAtual}0"
    if (
        Candidato != NickAtual
        and len(Candidato) <= 20
        and NICK_RE.match(Candidato)
        and not _NickOcupado(Candidato)
    ):
        return Candidato
    Base = Candidato if len(Candidato) <= 20 and NICK_RE.match(Candidato) else NickAtual
    return _ProximoNickLivre(Base, Ignorar=NickAtual)


def LiberarNickDeVisitante(NickDesejado: str) -> None:
    Conta = persistencia.ObterContaPorNick(NickDesejado)
    if not Conta:
        return
    if not Conta.get("eh_visitante"):
        raise ValueError("Este nick já está em uso.")
    NovoNick = _DeslocarNickVisitante(NickDesejado)
    persistencia.AtualizarNickConta(Conta["id"], NovoNick)


def MontarPerfilConta(Conta: dict) -> dict:
    from .progresso import MontarProgressoConta

    Pontos = int(Conta.get("pontos_ranqueada", PONTOS_INICIAIS))
    Elo = EloDePontos(Pontos)
    Perfil = {
        "idConta": Conta["id"],
        "nick": Conta["nick"],
        "avatarId": ResolverAvatarId(Conta.get("avatar_id"), Conta["nick"]),
        "email": Conta.get("email") or "",
        "ehVisitante": bool(Conta.get("eh_visitante")),
        "pontosRanqueada": Pontos,
        "elo": Elo,
        "eloNome": NomeEloExibicao(Elo),
        "partidasRanqueadas": int(Conta.get("partidas_ranqueadas", 0)),
        "vitoriasRanqueadas": int(Conta.get("vitorias_ranqueadas", 0)),
        "podeRanqueada": not bool(Conta.get("eh_visitante")),
    }
    if not Perfil["ehVisitante"]:
        Perfil["progresso"] = MontarProgressoConta(Conta["id"])
    return Perfil


def RegistrarConta(Nick: str, Email: str, Senha: str) -> tuple[dict, str]:
    N = ValidarNick(Nick)
    E = ValidarEmail(Email)
    ValidarSenha(Senha)
    LiberarNickDeVisitante(N)
    if persistencia.ObterContaPorNick(N):
        raise ValueError("Este nick já está em uso.")
    if persistencia.ObterContaPorEmail(E):
        raise ValueError("Este e-mail já está cadastrado.")
    Salt = secrets.token_hex(16)
    Hash = _HashSenha(Senha, Salt)
    IdConta = persistencia.CriarConta(
        N, Hash, Salt, EhVisitante=False, Email=E
    )
    Conta = persistencia.ObterContaPorId(IdConta)
    Token = persistencia.CriarSessao(
        IdConta, _AgoraUtc() + timedelta(days=DURACAO_SESSAO_DIAS)
    )
    return MontarPerfilConta(Conta), Token


def LoginConta(Identificador: str, Senha: str) -> tuple[dict, str]:
    ValidarSenha(Senha)
    Id = Identificador.strip()
    if "@" in Id:
        Conta = persistencia.ObterContaPorEmail(Id)
    else:
        try:
            N = ValidarNick(Id)
        except ValueError as Erro:
            raise ValueError("E-mail ou nick incorretos.") from Erro
        Conta = persistencia.ObterContaPorNick(N)
    if not Conta or Conta.get("eh_visitante"):
        raise ValueError("E-mail ou nick incorretos.")
    Hash = _HashSenha(Senha, Conta["senha_salt"])
    if not hmac.compare_digest(Hash, Conta["senha_hash"]):
        raise ValueError("E-mail ou nick incorretos.")
    Token = persistencia.CriarSessao(
        Conta["id"], _AgoraUtc() + timedelta(days=DURACAO_SESSAO_DIAS)
    )
    return MontarPerfilConta(Conta), Token


def EntrarComoVisitante(NickPreferido: str | None = None) -> tuple[dict, str]:
    Nick = ReservarNickVisitante(NickPreferido)
    _RemoverVisitanteInativoNoNick(Nick)
    IdConta = persistencia.CriarConta(
        Nick,
        senha_hash="",
        senha_salt="",
        EhVisitante=True,
        Email=None,
    )
    Conta = persistencia.ObterContaPorId(IdConta)
    Token = persistencia.CriarSessao(IdConta, _AgoraUtc() + timedelta(days=7))
    return MontarPerfilConta(Conta), Token


def DefinirAvatarConta(IdConta: str, AvatarId: str) -> dict:
    if not AvatarValido(AvatarId):
        raise ValueError("Escolha um avatar da lista.")
    persistencia.AtualizarAvatarConta(IdConta, AvatarId)
    Conta = persistencia.ObterContaPorId(IdConta)
    if not Conta:
        raise ValueError("Conta não encontrada.")
    return MontarPerfilConta(Conta)


def ResolverSessao(Token: str | None) -> dict | None:
    if not Token or len(Token) < 16:
        return None
    Sessao = persistencia.ObterSessaoPorToken(Token.strip())
    if not Sessao:
        return None
    Expira = datetime.fromisoformat(Sessao["expira_em"].replace("Z", "+00:00"))
    if Expira.tzinfo is None:
        Expira = Expira.replace(tzinfo=timezone.utc)
    if Expira < _AgoraUtc():
        persistencia.RevogarSessao(Token)
        return None
    Conta = persistencia.ObterContaPorId(Sessao["id_conta"])
    if not Conta:
        return None
    if Conta.get("eh_visitante"):
        persistencia.AtualizarAtividadeConta(Conta["id"])
    return MontarPerfilConta(Conta)


def ExigirContaRegistrada(Perfil: dict | None) -> dict:
    if not Perfil:
        raise ValueError("Faça login ou crie uma conta.")
    if Perfil.get("ehVisitante"):
        raise ValueError("Crie uma conta para usar ranking e modo ranqueado.")
    return Perfil


def ExigirPodeRanquear(Perfil: dict | None) -> dict:
    return ExigirContaRegistrada(Perfil)
