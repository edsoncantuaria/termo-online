from datetime import datetime, timedelta, timezone

import pytest

from nucleo import persistencia
from nucleo.contas import (
    EntrarComoVisitante,
    GerarNickVisitante,
    LiberarNickDeVisitante,
    NOMES_BASE_VISITANTE,
    RegistrarConta,
    ResolverSessao,
    ReservarNickVisitante,
    ValidarEmail,
    ValidarNick,
)


@pytest.fixture
def banco_contas(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "contas.db")
    persistencia.InicializarBanco()


def test_validar_nick_ok():
    assert ValidarNick("Jogador_1") == "jogador_1"


def test_validar_nick_invalido():
    with pytest.raises(ValueError):
        ValidarNick("ab")


def test_validar_email_ok():
    assert ValidarEmail("  User@Example.COM ") == "user@example.com"


def test_validar_email_invalido():
    with pytest.raises(ValueError):
        ValidarEmail("nao-email")


def test_visitante_escolhe_nick(banco_contas):
    Perfil, _ = EntrarComoVisitante("maria")
    assert Perfil["nick"] == "maria"
    Perfil2, _ = EntrarComoVisitante("maria")
    assert Perfil2["nick"] == "maria1"


def test_reservar_nick_invalido():
    with pytest.raises(ValueError):
        ReservarNickVisitante("ab")


def test_visitante_recebe_nick_amigavel(banco_contas):
    Perfil, _ = EntrarComoVisitante()
    assert Perfil["ehVisitante"] is True
    Base = Perfil["nick"].rstrip("0123456789")
    assert Base in NOMES_BASE_VISITANTE or Perfil["nick"].startswith("jogador")


def test_visitantes_sequenciais(banco_contas, monkeypatch):
    monkeypatch.setattr(
        "nucleo.contas.random.choice", lambda _: "maria"
    )
    persistencia.CriarConta("maria", "", "", EhVisitante=True)
    assert GerarNickVisitante() == "maria1"
    persistencia.CriarConta("maria1", "", "", EhVisitante=True)
    assert GerarNickVisitante() == "maria2"


def test_registro_toma_nick_de_visitante(banco_contas):
    IdVisitante = persistencia.CriarConta(
        "maria1", "", "", EhVisitante=True, Email=None
    )
    Perfil, _ = RegistrarConta("maria1", "nova@email.com", "senha12")
    assert Perfil["nick"] == "maria1"
    assert Perfil["ehVisitante"] is False
    Visitante = persistencia.ObterContaPorId(IdVisitante)
    assert Visitante["nick"] != "maria1"
    assert Visitante["nick"].startswith("maria1")


def test_registro_bloqueia_conta_real(banco_contas):
    persistencia.CriarConta(
        "joao",
        "hash",
        "salt",
        EhVisitante=False,
        Email="joao@email.com",
    )
    with pytest.raises(ValueError, match="nick"):
        RegistrarConta("joao", "outro@email.com", "senha12")


def test_liberar_visitante_desloca_com_zero(banco_contas):
    persistencia.CriarConta("ana", "", "", EhVisitante=True)
    LiberarNickDeVisitante("ana")
    assert persistencia.ObterContaPorNick("ana") is None
    Conta = persistencia.ObterContaPorNick("ana0")
    assert Conta is not None
    assert Conta["eh_visitante"]


def _MarcarVisitanteInativo(IdConta: str) -> None:
    Antiga = (
        datetime.now(timezone.utc)
        - timedelta(hours=persistencia.INATIVIDADE_VISITANTE_HORAS, minutes=5)
    ).isoformat()
    persistencia.AtualizarAtividadeConta(IdConta, Antiga)


def test_visitante_inativo_libera_nick(banco_contas):
    Perfil1, _ = EntrarComoVisitante("maria")
    assert Perfil1["nick"] == "maria"
    _MarcarVisitanteInativo(Perfil1["idConta"])
    Perfil2, _ = EntrarComoVisitante("maria")
    assert Perfil2["nick"] == "maria"
    assert Perfil2["idConta"] != Perfil1["idConta"]
    assert persistencia.ObterContaPorId(Perfil1["idConta"]) is None


def test_visitante_ativo_mantem_nick(banco_contas):
    Perfil1, _ = EntrarComoVisitante("maria")
    Perfil2, _ = EntrarComoVisitante("maria")
    assert Perfil2["nick"] == "maria1"


def test_sessao_visitante_renova_atividade(banco_contas):
    Perfil, Token = EntrarComoVisitante("lucas")
    _MarcarVisitanteInativo(Perfil["idConta"])
    assert ResolverSessao(Token) is not None
    Conta = persistencia.ObterContaPorId(Perfil["idConta"])
    assert not persistencia.VisitanteEstaInativo(Conta)
    Perfil2, _ = EntrarComoVisitante("lucas")
    assert Perfil2["nick"] == "lucas1"
