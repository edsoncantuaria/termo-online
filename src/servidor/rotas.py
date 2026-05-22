import random
import string
import uuid
from dataclasses import dataclass, field
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from nucleo.dicionario import ObterPalavraComAcento
from nucleo.estatisticas import ObterEstatisticasJogador
from nucleo.gerenciador_salas import (
    ConfiguracaoSala,
    FrasesChatPermitidas,
    MaximoCaracteresSenha,
    MaximoJogadoresPermitido,
    MinimoJogadoresSala,
    TempoLimiteMaximoSegundos,
)
from nucleo.logica_jogo import (
    AvaliarChute,
    MaximoTentativas,
    ModoDiaria,
    ModoPratica,
    PalavraFoiAcertada,
    ValidarPalavra,
)
from nucleo.modos_solo import (
    AvaliarChuteTabuleiros,
    ContarTentativasGlobais,
    CriarTabuleiros,
    DificuldadeDificil,
    DificuldadeNormal,
    MaximoTentativasModo,
    ModoDesafio,
    ModoDueto,
    ModoQuarteto,
    QuantidadePalavrasModo,
)
from nucleo import persistencia
from nucleo.arena_rodadas import FormatarModoSessao, ModoPontos, ModoVitorias
from nucleo.palavra_diaria import EscolherPalavraDoDia
from nucleo.contas import (
    EntrarComoVisitante,
    LoginConta,
    MontarPerfilConta,
    RegistrarConta,
    ResolverSessao,
)
from nucleo.matchmaking import FilaGlobal
from nucleo.pontuacao import CalcularPontuacao, ObterRanking, RegistrarPontuacao
from nucleo.ranqueada import ELOS, EloDePontos, NomeEloExibicao
from servidor.dependencias_auth import ContaObrigatoria, ContaOpcional, ContaRegistrada
from servidor.estado_global import GerenciadorVersus
from servidor.websocket import BroadcastEstadoSala


@dataclass
class PartidaSolo:
    IdPartida: str
    PalavraSecreta: str
    PalavraComAcento: str
    Modo: str = ModoPratica
    DataDia: str | None = None
    Tentativas: list[dict] = field(default_factory=list)
    Tabuleiros: list[dict] = field(default_factory=list)
    Dificuldade: str = DificuldadeNormal
    CodigoDesafio: str | None = None
    Encerrada: bool = False
    Venceu: bool = False
    NomeJogador: str = "Jogador"
    IdConta: str | None = None


def MontarRespostaPartida(Partida: PartidaSolo) -> dict:
    MaxTent = MaximoTentativasModo(Partida.Modo)
    Usadas = (
        ContarTentativasGlobais(Partida.Tabuleiros)
        if Partida.Tabuleiros
        else len(Partida.Tentativas)
    )
    return {
        "idPartida": Partida.IdPartida,
        "modo": Partida.Modo,
        "dataDia": Partida.DataDia,
        "dificuldade": Partida.Dificuldade,
        "codigoDesafio": Partida.CodigoDesafio,
        "maximoTentativas": MaxTent,
        "tentativasUsadas": Usadas,
        "encerrada": Partida.Encerrada,
        "venceu": Partida.Venceu,
        "tentativas": Partida.Tentativas,
        "tabuleiros": Partida.Tabuleiros or None,
        "quantidadePalavras": QuantidadePalavrasModo(Partida.Modo),
    }


PartidasSolo: dict[str, PartidaSolo] = {}


def ObterPartida(IdPartida: str) -> PartidaSolo | None:
    if IdPartida not in PartidasSolo:
        Carregada = persistencia.CarregarPartidaSolo(IdPartida, PartidaSolo)
        if Carregada:
            PartidasSolo[IdPartida] = Carregada
    return PartidasSolo.get(IdPartida)


def SalvarPartida(Partida: PartidaSolo) -> None:
    PartidasSolo[Partida.IdPartida] = Partida
    persistencia.SalvarPartidaSolo(Partida)


class IniciarJogoRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)
    modo: Literal["diaria", "pratica", "dueto", "quarteto", "desafio"] = ModoPratica
    dificuldade: Literal["normal", "dificil"] = DificuldadeNormal
    codigoDesafio: str | None = Field(default=None, max_length=8)


class IniciarSoloRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)


class ChuteSoloRequest(BaseModel):
    idPartida: str
    palavra: str
    nomeJogador: str = Field(default="Jogador", max_length=24)


class CriarSalaRequest(BaseModel):
    nomeJogador: str = Field(default="Jogador", max_length=24)
    mesmaPalavra: bool = True
    verOutros: bool = True
    maximoJogadores: int = Field(default=4, ge=MinimoJogadoresSala, le=MaximoJogadoresPermitido)
    senha: str | None = Field(default=None, max_length=MaximoCaracteresSenha)
    tempoLimiteSegundos: int = Field(default=180, ge=0, le=TempoLimiteMaximoSegundos)
    numeroRodadas: int = Field(default=0, ge=0, le=100)
    modoSessao: str = Field(default=ModoPontos)
    metaVitorias: int = Field(default=5, ge=1, le=20)
    inicioAutoDois: bool = False
    salaPublica: bool = True


class EntrarSalaRequest(BaseModel):
    codigoSala: str = Field(min_length=6, max_length=6)
    nomeJogador: str = Field(default="Jogador", max_length=24)
    senha: str | None = Field(default=None, max_length=MaximoCaracteresSenha)
    espectador: bool = False


class SairSalaRequest(BaseModel):
    codigoSala: str = Field(min_length=6, max_length=6)
    idJogador: str


class RegistrarPontosRequest(BaseModel):
    nomeJogador: str = Field(max_length=24)
    pontos: int = Field(ge=0)
    modo: str = Field(default="solo")
    tentativasUsadas: int = Field(ge=1, le=6)
    venceu: bool


class GradeDiariaRequest(BaseModel):
    nick: str = Field(max_length=24)
    gradeTexto: str = ""
    venceu: bool = False
    tentativasUsadas: int = Field(ge=1, le=6)
    pontos: int = Field(default=0, ge=0)


class AuthLoginRequest(BaseModel):
    identificador: str = Field(min_length=3, max_length=120)
    senha: str = Field(min_length=6, max_length=64)


class AuthRegistroRequest(BaseModel):
    nick: str = Field(min_length=3, max_length=20)
    email: str = Field(min_length=5, max_length=120)
    senha: str = Field(min_length=6, max_length=64)


class AuthVisitanteRequest(BaseModel):
    nick: str | None = Field(default=None, min_length=3, max_length=20)


def MontarRespostaSala(Sala, Jogador) -> dict:
    Resposta = GerenciadorVersus.EstadoPublicoSala(Sala, Jogador.IdJogador)
    Resposta["idJogador"] = Jogador.IdJogador
    Resposta["nomeJogador"] = Jogador.NomeJogador
    return Resposta


def RegistrarRotas(Aplicacao) -> None:
    Roteador = APIRouter(prefix="/api")

    @Roteador.get("/ranking")
    def ObterRankingEndpoint():
        return {"ranking": ObterRanking()}

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

    @Roteador.get("/ranqueada/matchmaking")
    def InfoMatchmakingRanqueado():
        from nucleo.matchmaking_competitivo import (
            BUSCA_REAL_SEG,
            ESPERA_BOT_SEG,
            JANELA_RP_CRESCIMENTO_POR_SEG,
            JANELA_RP_INICIAL,
            JANELA_RP_MAXIMA,
            JANELA_RP_MESMO_ELO_EXTRA,
        )

        return {
            "janelaRpInicial": JANELA_RP_INICIAL,
            "crescimentoRpPorSegundo": JANELA_RP_CRESCIMENTO_POR_SEG,
            "janelaRpMaxima": JANELA_RP_MAXIMA,
            "bonusMesmoEloRp": JANELA_RP_MESMO_ELO_EXTRA,
            "buscaRealSegundos": BUSCA_REAL_SEG,
            "esperaOponenteSegundos": ESPERA_BOT_SEG,
            "descricao": (
                "Janela ±RP começa apertada e cresce na fila; "
                "pareia o oponente mais próximo dentro da janela."
            ),
        }

    @Roteador.get("/ranqueada/elos")
    def ListarElos():
        return {
            "elos": [
                {
                    "id": E[0],
                    "nome": NomeEloExibicao(E[0]),
                    "minimo": E[1],
                    "maximo": E[2],
                }
                for E in ELOS
            ]
        }

    @Roteador.get("/ranqueada/ranking")
    def RankingRanqueado(Perfil=Depends(ContaRegistrada)):
        from nucleo.ranking_ranqueado import MontarRankingCompleto

        return MontarRankingCompleto(Perfil)

    @Roteador.post("/ranqueada/fila")
    async def RanqueadaEntrarFila(Perfil=Depends(ContaRegistrada)):
        Status = FilaGlobal.Entrar(Perfil, GerenciadorVersus)
        if Status.get("estado") == "encontrado" and Status.get("codigoSala"):
            Sala = GerenciadorVersus.ObterSala(Status["codigoSala"])
            if Sala:
                await BroadcastEstadoSala(Sala)
        return Status

    @Roteador.delete("/ranqueada/fila")
    def RanqueadaSairFila(Perfil=Depends(ContaRegistrada)):
        FilaGlobal.Sair(Perfil["idConta"])
        return {"saiu": True}

    @Roteador.get("/ranqueada/fila")
    def RanqueadaStatusFila(Perfil=Depends(ContaRegistrada)):
        return FilaGlobal.Status(Perfil["idConta"], GerenciadorVersus)

    @Roteador.get("/diaria/info")
    def InfoPalavraDiaria(nick: str = "Jogador", Perfil=Depends(ContaOpcional)):
        _, _, DataDia = EscolherPalavraDoDia()
        IdConta = Perfil["idConta"] if Perfil and not Perfil.get("ehVisitante") else None
        JaJogou = persistencia.JaConcluiuDiariaHoje(IdConta, nick, DataDia)
        Registro = persistencia.ObterDiariaJogadorPorConta(IdConta, DataDia) if IdConta else None
        if not Registro:
            Registro = persistencia.ObterDiariaJogador(nick, DataDia)
        return {
            "dataDia": DataDia,
            "maximoTentativas": MaximoTentativas,
            "descricao": "Uma palavra por dia. Todo mundo joga a mesma — compare com amigos.",
            "jaJogou": JaJogou,
            "exigeConta": True,
            "resultado": (
                {
                    "venceu": bool(Registro["venceu"]),
                    "tentativasUsadas": Registro["tentativas_usadas"],
                    "gradeTexto": Registro.get("grade_texto"),
                    "pontos": Registro["pontos"],
                }
                if Registro
                else None
            ),
        }

    def IniciarPartida(Corpo: IniciarJogoRequest, Perfil: dict | None = None) -> dict:
        Nome = Corpo.nomeJogador[:24] or "Jogador"
        DataDia = None
        CodigoDesafio = (Corpo.codigoDesafio or "").strip().upper()[:8] or None
        IdConta = None
        if Perfil and not Perfil.get("ehVisitante"):
            IdConta = Perfil["idConta"]

        if Corpo.modo == ModoDiaria:
            _, _, DataDia = EscolherPalavraDoDia()
            if persistencia.JaConcluiuDiariaHoje(IdConta, Nome, DataDia):
                raise HTTPException(
                    status_code=400,
                    detail="Você já jogou a palavra do dia hoje. Volte amanhã!",
                )
            if IdConta:
                Sessao = persistencia.ObterSessaoDiariaConta(IdConta, DataDia)
                if Sessao and Sessao.get("encerrada"):
                    raise HTTPException(
                        status_code=400,
                        detail="Palavra do dia já concluída nesta conta.",
                    )
            Tabuleiros = CriarTabuleiros(ModoDiaria, Corpo.dificuldade)
        elif Corpo.modo == ModoDesafio:
            if not CodigoDesafio:
                raise HTTPException(status_code=400, detail="Informe o código do desafio.")
            Tabuleiros = CriarTabuleiros(ModoDesafio, Corpo.dificuldade, CodigoDesafio)
        else:
            Tabuleiros = CriarTabuleiros(Corpo.modo, Corpo.dificuldade, CodigoDesafio)

        IdPartida = str(uuid.uuid4())
        Partida = PartidaSolo(
            IdPartida=IdPartida,
            PalavraSecreta=Tabuleiros[0]["palavraSecreta"],
            PalavraComAcento=Tabuleiros[0]["palavraComAcento"],
            Modo=Corpo.modo,
            DataDia=DataDia,
            NomeJogador=Nome,
            Tabuleiros=Tabuleiros,
            Dificuldade=Corpo.dificuldade,
            CodigoDesafio=CodigoDesafio,
            IdConta=IdConta,
        )
        SalvarPartida(Partida)
        if Corpo.modo == ModoDiaria and IdConta and DataDia:
            persistencia.IniciarSessaoDiariaConta(IdConta, DataDia, IdPartida)
        Resposta = MontarRespostaPartida(Partida)
        Resposta["nomeJogador"] = Nome
        return Resposta

    @Roteador.post("/jogar/iniciar")
    def IniciarJogo(Corpo: IniciarJogoRequest, Perfil=Depends(ContaOpcional)):
        return IniciarPartida(Corpo, Perfil)

    @Roteador.post("/solo/iniciar")
    def IniciarPartidaSolo(Corpo: IniciarSoloRequest):
        return IniciarPartida(
            IniciarJogoRequest(nomeJogador=Corpo.nomeJogador, modo=ModoPratica)
        )

    @Roteador.post("/solo/chute")
    def EnviarChuteSolo(Corpo: ChuteSoloRequest, Perfil=Depends(ContaOpcional)):
        from nucleo.progresso import RecompensaDiariaChute, RecompensaPraticaChute

        Partida = ObterPartida(Corpo.idPartida)
        if not Partida:
            raise HTTPException(status_code=404, detail="Partida não encontrada.")
        if Partida.Encerrada:
            raise HTTPException(status_code=400, detail="Partida já encerrada.")
        IdConta = Partida.IdConta
        if Perfil and not Perfil.get("ehVisitante"):
            if not IdConta:
                IdConta = Perfil["idConta"]
                Partida.IdConta = IdConta
            elif IdConta != Perfil["idConta"]:
                raise HTTPException(status_code=403, detail="Partida de outra conta.")
        if Partida.Modo == ModoDiaria and Partida.DataDia:
            if persistencia.JaConcluiuDiariaHoje(
                IdConta, Corpo.nomeJogador, Partida.DataDia
            ):
                raise HTTPException(status_code=400, detail="Palavra do dia já concluída.")

        Valido, MensagemOuPalavra = ValidarPalavra(Corpo.palavra)
        if not Valido:
            return {"valido": False, "mensagem": MensagemOuPalavra}

        PalavraNormalizada = MensagemOuPalavra
        MaxTent = MaximoTentativasModo(Partida.Modo)

        if Partida.Tabuleiros and len(Partida.Tabuleiros) > 1:
            Resultado = AvaliarChuteTabuleiros(Partida.Tabuleiros, PalavraNormalizada)
            PalavraExibicao = ObterPalavraComAcento(PalavraNormalizada) or PalavraNormalizada
            Tentativa = {
                "palavra": PalavraExibicao,
                "letras": list(PalavraExibicao.upper()),
                "linhas": Resultado["linhas"],
            }
            Partida.Tentativas.append(Tentativa)
            Acertou = Resultado["todasVencidas"]
            TentativasUsadas = ContarTentativasGlobais(Partida.Tabuleiros)
        else:
            Estados = [E.value for E in AvaliarChute(Partida.PalavraSecreta, PalavraNormalizada)]
            PalavraExibicao = ObterPalavraComAcento(PalavraNormalizada) or PalavraNormalizada
            Tentativa = {
                "palavra": PalavraExibicao,
                "letras": list(PalavraExibicao.upper()),
                "estados": Estados,
            }
            Partida.Tentativas.append(Tentativa)
            Acertou = PalavraFoiAcertada(Partida.PalavraSecreta, PalavraNormalizada)
            TentativasUsadas = len(Partida.Tentativas)

        if Acertou:
            Partida.Encerrada = True
            Partida.Venceu = True
        elif TentativasUsadas >= MaxTent:
            Partida.Encerrada = True

        Pontos = 0
        if Partida.Encerrada:
            ModoRank = Partida.Modo if Partida.Modo != ModoDesafio else ModoPratica
            Pontos = CalcularPontuacao(Partida.Venceu, TentativasUsadas, ModoRank)
            RegistrarPontuacao(
                Corpo.nomeJogador,
                Pontos,
                ModoRank,
                TentativasUsadas,
                Partida.Venceu,
            )
            if Partida.Modo == ModoDiaria and Partida.DataDia:
                persistencia.RegistrarDiaria(
                    Corpo.nomeJogador,
                    Partida.DataDia,
                    Partida.Venceu,
                    TentativasUsadas,
                    Pontos,
                    IdConta=IdConta,
                )
        Partida.NomeJogador = Corpo.nomeJogador[:24] or "Jogador"
        SalvarPartida(Partida)

        ProgressoXp = None
        if IdConta and (not Perfil or not Perfil.get("ehVisitante")):
            IndiceTent = TentativasUsadas - 1
            if Partida.Modo == ModoDiaria and Partida.DataDia:
                ProgressoXp = RecompensaDiariaChute(
                    IdConta,
                    Partida.DataDia,
                    Partida.IdPartida,
                    IndiceTent,
                    Acertou,
                    Partida.Encerrada,
                    Partida.Venceu,
                )
            elif Partida.Modo == ModoPratica:
                ProgressoXp = RecompensaPraticaChute(
                    IdConta, Partida.Encerrada, Partida.Venceu
                )

        Resposta = {
            "valido": True,
            "tentativa": Tentativa,
            "tentativasUsadas": TentativasUsadas,
            "maximoTentativas": MaxTent,
            "modo": Partida.Modo,
            "dataDia": Partida.DataDia,
            "encerrada": Partida.Encerrada,
            "venceu": Partida.Venceu,
            "pontos": Pontos,
            "tentativas": Partida.Tentativas,
            "tabuleiros": Partida.Tabuleiros or None,
        }
        if Partida.Encerrada:
            if Partida.Tabuleiros:
                Resposta["palavrasSecretas"] = [T["palavraComAcento"] for T in Partida.Tabuleiros]
            else:
                Resposta["palavraSecreta"] = Partida.PalavraComAcento
        if ProgressoXp:
            Resposta["progresso"] = ProgressoXp
        return Resposta

    @Roteador.post("/jogar/chute")
    def EnviarChuteJogo(Corpo: ChuteSoloRequest, Perfil=Depends(ContaOpcional)):
        return EnviarChuteSolo(Corpo, Perfil)

    @Roteador.get("/progresso/eu")
    def ProgressoEu(Perfil=Depends(ContaRegistrada)):
        from nucleo.progresso import MontarProgressoConta

        return MontarProgressoConta(Perfil["idConta"])

    @Roteador.get("/jogar/estado/{id_partida}")
    def EstadoPartida(id_partida: str):
        Partida = ObterPartida(id_partida)
        if not Partida:
            raise HTTPException(status_code=404, detail="Partida não encontrada.")
        return MontarRespostaPartida(Partida)

    @Roteador.post("/sala/criar")
    async def CriarSala(Corpo: CriarSalaRequest, Perfil=Depends(ContaOpcional)):
        try:
            Modo = Corpo.modoSessao if Corpo.modoSessao in (ModoPontos, ModoVitorias) else ModoPontos
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

    @Roteador.post("/diaria/grade")
    def SalvarGradeDiaria(Corpo: GradeDiariaRequest):
        _, _, DataDia = EscolherPalavraDoDia()
        persistencia.RegistrarDiaria(
            Corpo.nick,
            DataDia,
            Corpo.venceu,
            Corpo.tentativasUsadas,
            Corpo.pontos,
            Corpo.gradeTexto or None,
        )
        return {"salvo": True}

    @Roteador.get("/salas/publicas")
    def SalasPublicas():
        GerenciadorVersus.RestaurarSalasAtivas()
        return {"salas": GerenciadorVersus.ListarSalasPublicas()}

    @Roteador.get("/stats")
    def Estatisticas(nick: str = "Jogador"):
        return ObterEstatisticasJogador(nick)

    @Roteador.get("/diaria/historico")
    def HistoricoDiaria(nick: str = "Jogador"):
        NickNorm = nick.strip()[:24].lower() or "jogador"
        return {"historico": persistencia.ListarHistoricoDiaria(NickNorm, 30)}

    @Roteador.post("/desafio/criar")
    def CriarDesafio():
        Codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return {"codigoDesafio": Codigo, "link": f"/?desafio={Codigo}"}

    @Roteador.get("/arena/frases-chat")
    def FrasesChat():
        return {"frases": list(FrasesChatPermitidas)}

    @Roteador.post("/pontuacao/registrar")
    def RegistrarPontuacaoEndpoint():
        raise HTTPException(
            status_code=403,
            detail="Pontuação é calculada apenas no servidor.",
        )

    Aplicacao.include_router(Roteador)
