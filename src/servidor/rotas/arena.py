import random
import string

from fastapi import APIRouter, Depends, HTTPException

from nucleo.arena_rodadas import ModoPontos, ModoVitorias
from nucleo.controle_carga import PodeCriarSala
from nucleo.gerenciador_salas import ConfiguracaoSala
from nucleo.redis_estado import VerificarWorkerDonoSala
from nucleo.sala_chat import FrasesChatPermitidas
from servidor.dependencias_auth import ContaOpcional
from servidor.estado_global import GerenciadorVersus
from servidor.rotas.schemas import (
    CriarSalaRequest,
    EntrarSalaRequest,
    MontarRespostaSala,
    SairSalaRequest,
)
from servidor.websocket import BroadcastEstadoSala


def RegistrarRotasArena(Roteador: APIRouter) -> None:
    @Roteador.post("/sala/criar")
    async def CriarSala(Corpo: CriarSalaRequest, Perfil=Depends(ContaOpcional)):
        Admissao = PodeCriarSala(len(GerenciadorVersus.Salas))
        if not Admissao.Permitido:
            raise HTTPException(
                status_code=503,
                detail=Admissao.Mensagem,
                headers={"Retry-After": str(Admissao.RetryAfterSegundos)},
            )
        try:
            Modo = (
                Corpo.modoSessao
                if Corpo.modoSessao in (ModoPontos, ModoVitorias)
                else ModoPontos
            )
            Config = ConfiguracaoSala(
                MesmaPalavra=Corpo.mesmaPalavra,
                VerOutros=Corpo.verOutros,
                MaximoJogadores=Corpo.maximoJogadores,
                Senha=Corpo.senha,
                TempoLimiteSegundos=Corpo.tempoLimiteSegundos,
                NumeroRodadas=0,
                ModoSessao=Modo,
                MetaVitorias=Corpo.metaVitorias,
                InicioAutoDois=Corpo.inicioAutoDois,
                SalaPublica=Corpo.salaPublica,
            )
            Nome = Corpo.nomeJogador[:24] or "Jogador"
            IdConta = None
            if Perfil:
                Nome = Perfil["nick"][:24]
                IdConta = Perfil["idConta"]
            Sala, Jogador = GerenciadorVersus.CriarSala(Nome, Config, IdConta=IdConta)
        except ValueError as Erro:
            raise HTTPException(status_code=400, detail=str(Erro)) from Erro
        await BroadcastEstadoSala(Sala)
        return MontarRespostaSala(Sala, Jogador)

    @Roteador.post("/sala/entrar")
    async def EntrarSala(Corpo: EntrarSalaRequest, Perfil=Depends(ContaOpcional)):
        Codigo = Corpo.codigoSala.upper()
        DonoOk, WorkerRemoto = VerificarWorkerDonoSala(Codigo)
        if not DonoOk:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Esta sala está em outro processo da API. "
                    "Mantenha um único termo-api na VM (tunnel → :8001)."
                ),
                headers={"X-Termo-Worker": WorkerRemoto or ""},
            )
        Nome = Corpo.nomeJogador[:24] or "Jogador"
        IdConta = None
        if Perfil:
            Nome = Perfil["nick"][:24]
            IdConta = Perfil["idConta"]
        Sala, Jogador, Erro = GerenciadorVersus.EntrarSala(
            Corpo.codigoSala.upper(),
            Nome,
            Corpo.senha,
            Corpo.espectador,
            IdConta=IdConta,
        )
        if Erro:
            raise HTTPException(status_code=400, detail=Erro)
        GerenciadorVersus.TentarInicioAutomatico(Sala)
        Sala = GerenciadorVersus.ObterSala(Sala.CodigoSala) or Sala
        await BroadcastEstadoSala(Sala)
        Resposta = MontarRespostaSala(Sala, Jogador)
        Resposta["aguardandoInicio"] = Sala.EstadoSala == "aguardando"
        return Resposta

    @Roteador.get("/sala/{codigo_sala}/convite")
    def ConviteSala(codigo_sala: str):
        GerenciadorVersus.RestaurarSalasAtivas()
        Info = GerenciadorVersus.InfoConviteSala(codigo_sala)
        if not Info:
            raise HTTPException(status_code=404, detail="Sala não encontrada.")
        return Info

    @Roteador.get("/sala/{codigo_sala}")
    def ConsultarSala(codigo_sala: str, id_jogador: str):
        Sala = GerenciadorVersus.ObterSala(codigo_sala)
        if not Sala or id_jogador not in Sala.Jogadores:
            raise HTTPException(status_code=404, detail="Sala não encontrada.")
        return GerenciadorVersus.EstadoPublicoSala(Sala, id_jogador)

    @Roteador.post("/sala/sair")
    async def SairSala(Corpo: SairSalaRequest):
        Sala = GerenciadorVersus.ObterSala(Corpo.codigoSala)
        if not Sala or Corpo.idJogador not in Sala.Jogadores:
            raise HTTPException(status_code=404, detail="Sala não encontrada.")
        Codigo = Sala.CodigoSala
        GerenciadorVersus.RemoverJogador(Codigo, Corpo.idJogador)
        SalaAtual = GerenciadorVersus.ObterSala(Codigo)
        if SalaAtual:
            await BroadcastEstadoSala(SalaAtual)
        return {"saiu": True}

    @Roteador.get("/salas/publicas")
    def SalasPublicas():
        GerenciadorVersus.RestaurarSalasAtivas()
        return {"salas": GerenciadorVersus.ListarSalasPublicas()}

    @Roteador.post("/desafio/criar")
    def CriarDesafio():
        Codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return {"codigoDesafio": Codigo, "link": f"/?desafio={Codigo}"}

    @Roteador.get("/arena/frases-chat")
    def FrasesChat():
        return {"frases": list(FrasesChatPermitidas)}
