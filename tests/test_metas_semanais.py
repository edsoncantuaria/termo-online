from nucleo import persistencia
from nucleo.metas_semanais import METAS_SEMANAIS, MontarMetasSemanaisConta
from nucleo.progresso import RecompensaArenaRodada
from nucleo.tempo_brasil import SemanaIsoBrasil


def test_meta_semanal_arena(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "m.db")
    persistencia.InicializarBanco()
    from nucleo.contas import RegistrarConta

    Perfil, _ = RegistrarConta("meta_a", "meta@test.com", "senha123")
    Id = Perfil["idConta"]
    Meta = next(M for M in METAS_SEMANAIS if M["id"] == "arena_5")
    for I in range(Meta["meta"]):
        RecompensaArenaRodada(Id, f"S{I}", I + 1, I % 2 == 0)
    Lista = MontarMetasSemanaisConta(Id)
    Arena = next(L for L in Lista if L["id"] == "arena_5")
    assert Arena["concluida"]
    assert "arena_5" in persistencia.ListarMetasSemanaisRecompensadas(Id, SemanaIsoBrasil())
