from nucleo import persistencia
from nucleo.pontuacao import ObterRanking, RegistrarPontuacao


def test_visitante_nao_entra_ranking_casual(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia, "CaminhoBanco", tmp_path / "r.db")
    persistencia.InicializarBanco()
    from nucleo.contas import EntrarComoVisitante, RegistrarConta

    V, _ = EntrarComoVisitante("teste2")
    assert V["ehVisitante"]
    assert RegistrarPontuacao("teste2", 0, "pratica", 6, False) is None
    assert RegistrarPontuacao("teste2", 500, "pratica", 3, True) is None

    Perfil, _ = RegistrarConta("real_rank", "rank@test.com", "senha123")
    assert RegistrarPontuacao(
        Perfil["nick"], 800, "pratica", 2, True, IdConta=Perfil["idConta"]
    )

    Ranking = ObterRanking()
    Nicks = [R["nome_jogador"] for R in Ranking]
    assert "teste2" not in Nicks
    assert Perfil["nick"] in Nicks
