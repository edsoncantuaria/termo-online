import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nucleo.avatares import AvatarPadraoDeNick, AvatarValido, AVATARES
from nucleo.contas import DefinirAvatarConta, RegistrarConta
from nucleo import persistencia


@pytest.fixture
def banco(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "av.db")
    persistencia.InicializarBanco()
    yield


def test_avatar_valido():
    assert AvatarValido("folha")
    assert not AvatarValido("inexistente")


def test_avatar_padrao_estavel():
    assert AvatarPadraoDeNick("maria") == AvatarPadraoDeNick("maria")
    assert AvatarPadraoDeNick("maria") in AVATARES


def test_definir_avatar_conta(banco):
    Perfil, _ = RegistrarConta("avatar_u", "av@test.com", "senha123")
    Atualizado = DefinirAvatarConta(Perfil["idConta"], "coruja")
    assert Atualizado["avatarId"] == "coruja"
    Conta = persistencia.ObterContaPorId(Perfil["idConta"])
    assert Conta["avatar_id"] == "coruja"


def test_definir_avatar_invalido(banco):
    Perfil, _ = RegistrarConta("avatar_inv", "inv@test.com", "senha123")
    with pytest.raises(ValueError, match="lista"):
        DefinirAvatarConta(Perfil["idConta"], "xyz")
