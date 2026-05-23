from fastapi import APIRouter, Depends, HTTPException

from nucleo.dicionario import ObterHashDicionario
from nucleo.estatisticas import ObterEstatisticasJogador
from nucleo.pontuacao import ObterRanking
from servidor.dependencias_auth import ContaOpcional
from servidor.metricas import MontarSnapshotMetricas


def RegistrarRotasMisc(Roteador: APIRouter) -> None:
    @Roteador.get("/ranking")
    def ObterRankingEndpoint():
        return {"ranking": ObterRanking()}

    @Roteador.get("/stats")
    def Estatisticas(nick: str = "Jogador", Perfil=Depends(ContaOpcional)):
        IdConta = (
            Perfil["idConta"]
            if Perfil and not Perfil.get("ehVisitante")
            else None
        )
        return ObterEstatisticasJogador(nick, IdConta=IdConta, Perfil=Perfil)

    @Roteador.get("/dicionario/info")
    def InfoDicionario():
        from nucleo.dicionario import ObterDicionario

        _, Palavras, _ = ObterDicionario()
        return {
            "hash": ObterHashDicionario(),
            "total": len(Palavras),
            "tamanhoPalavra": 5,
        }

    @Roteador.get("/dicionario/palavras")
    def ListaPalavrasDicionario():
        from nucleo.dicionario import ObterDicionario

        _, Palavras, _ = ObterDicionario()
        return {"hash": ObterHashDicionario(), "palavras": Palavras}

    @Roteador.get("/metricas")
    def Metricas():
        return MontarSnapshotMetricas()

    @Roteador.post("/pontuacao/registrar")
    def RegistrarPontuacaoEndpoint():
        raise HTTPException(
            status_code=403,
            detail="Pontuação é calculada apenas no servidor.",
        )
