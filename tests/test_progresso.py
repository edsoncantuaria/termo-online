from nucleo.progresso import (
    CAP_XP_DIARIO,
    CalcularEstadoNivel,
    MultiplicadorXpGanho,
    RecompensaDiariaChute,
    XpBrutoParaEfetivo,
    XpParaSubirNivel,
    _ConcederXp,
)
from nucleo import persistencia


def test_nivel_infinito_cresce():
    assert XpParaSubirNivel(1) < XpParaSubirNivel(50)
    assert XpParaSubirNivel(1) == 50
    E100 = CalcularEstadoNivel(50_000)
    assert E100.Nivel > 30


def test_xp_comeca_rapido_e_fica_mais_dificil():
    assert MultiplicadorXpGanho(1) == 1.0
    assert MultiplicadorXpGanho(30) < MultiplicadorXpGanho(5)
    assert XpBrutoParaEfetivo(1, 10) == 10
    assert XpBrutoParaEfetivo(40, 10) < 10


def test_cap_diario_xp(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "cap.db")
    persistencia.InicializarBanco()
    from nucleo.contas import RegistrarConta

    Perfil, _ = RegistrarConta("cap_xp", "cap@test.com", "senha123")
    Id = Perfil["idConta"]
    persistencia.AdicionarXpConta(Id, 500_000)
    persistencia.RegistrarXpGanhoDiario(Id, CAP_XP_DIARIO - 1)
    R = _ConcederXp(Id, 50, "teste")
    assert R is not None
    assert R["xpGanho"] == 1
    R2 = _ConcederXp(Id, 50, "teste2")
    assert R2 is not None
    assert R2["xpGanho"] == 0
    assert R2["xpCapAtingido"] is True


def test_diaria_xp_uma_vez_por_tentativa(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "t.db")
    persistencia.InicializarBanco()
    from nucleo.contas import RegistrarConta

    Perfil, _ = RegistrarConta("xp_test", "xp@test.com", "senha123")
    Id = Perfil["idConta"]
    Data = "2099-01-15"
    Partida = "part-1"
    persistencia.IniciarSessaoDiariaConta(Id, Data, Partida)

    R1 = RecompensaDiariaChute(Id, Data, Partida, 0, False, False, False)
    R2 = RecompensaDiariaChute(Id, Data, Partida, 0, False, False, False)
    assert R1 is not None
    assert R2 is None

    R3 = RecompensaDiariaChute(Id, Data, Partida, 1, True, True, True)
    assert R3 is not None
    assert persistencia.JaDesbloqueouBadge(Id, "diaria_venceu")
