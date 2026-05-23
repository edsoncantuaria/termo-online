import hashlib
import random
import secrets
import string
import time
import uuid
from dataclasses import dataclass, field

from . import persistencia
from .avatares import ResolverAvatarId
from .arena_rodadas import (
    CalcularPontosRodada,
    DeterminarCampeaoSessao,
    DeterminarVencedorRodada,
    DeterminarVencedoresRodadaPorVerdes,
    FormatarModoSessao,
    MontarMensagemFimRodada,
    JogadorAtingiuMetaVitorias,
    MelhorContagemVerdes,
    ModoPontos,
    ModoVitorias,
    MontarPlacar,
    SessaoAtingiuLimite,
)
from .dicionario import ObterPalavraComAcento
from .sala_chat import (
    AdicionarMensagemChatSala,
    FrasesChatPermitidas,
    MaximoMensagensChat,
)
from .logica_jogo import (
    AvaliarChute,
    EscolherPalavraAleatoria,
    MaximoTentativas,
    PalavraFoiAcertada,
)

MinimoJogadoresSala = 2
MaximoJogadoresPermitido = 8
MaximoCaracteresSenha = 8
TempoLimiteMinimoSegundos = 60
TempoLimiteMaximoSegundos = 900
TempoInativoSegundos = 300
MaximoEspectadores = 6
SegundosCountdown = 3
_NotificarLobbySalas = None


def RegistrarNotificadorLobbySalas(Callback) -> None:
    global _NotificarLobbySalas
    _NotificarLobbySalas = Callback


def _DispararNotificacaoLobby() -> None:
    if _NotificarLobbySalas:
        _NotificarLobbySalas()


@dataclass
class ConfiguracaoSala:
    MesmaPalavra: bool = True
    VerOutros: bool = True
    MaximoJogadores: int = 4
    Senha: str | None = None
    TempoLimiteSegundos: int = 0
    NumeroRodadas: int = 0
    ModoSessao: str = ModoPontos
    MetaVitorias: int = 5
    InicioAutoDois: bool = False
    SalaPublica: bool = True
    Ranqueada: bool = False
    EhDesafio: bool = False


@dataclass
class JogadorSala:
    IdJogador: str
    NomeJogador: str
    PalavraSecreta: str | None = None
    PalavraComAcento: str | None = None
    Tentativas: list[dict] = field(default_factory=list)
    Venceu: bool = False
    Finalizou: bool = False
    Pontos: int = 0
    TempoFimEpoch: float | None = None
    Conectado: bool = False
    UltimaAtividade: float = field(default_factory=time.time)
    PontosAcumulados: int = 0
    PontosUltimaRodada: int = 0
    VitoriasRodada: int = 0
    Espectador: bool = False
    IdConta: str | None = None
    Pronto: bool = False
    EhBot: bool = False
    TokenSessao: str | None = None
    AusenteContinua: bool = False
    DesconexaoInicioEpoch: float | None = None


@dataclass
class SalaJogo:
    CodigoSala: str
    CriadorId: str
    Configuracao: ConfiguracaoSala
    IdPartida: str = field(default_factory=lambda: str(uuid.uuid4()))
    EstadoSala: str = "aguardando"
    EstadoSalaAntesPausa: str | None = None
    PausaAteEpoch: float | None = None
    IdJogadorPausado: str | None = None
    TimersCongelados: dict[str, float] = field(default_factory=dict)
    PalavraSecreta: str | None = None
    PalavraComAcento: str | None = None
    Jogadores: dict[str, JogadorSala] = field(default_factory=dict)
    PartidaEncerrada: bool = False
    PartidaCancelada: bool = False
    VencedorId: str | None = None
    RodadaAtual: int = 0
    HistoricoRodadas: list[dict] = field(default_factory=list)
    MensagensChat: list[dict] = field(default_factory=list)
    CountdownFimEpoch: float | None = None
    UltimoVencedorRodadaId: str | None = None
    ResultadosRanqueada: list[dict] | None = None
    PendentesXpConta: dict[str, dict] = field(default_factory=dict)


from . import sala_persistencia as _sala_persistencia


class GerenciadorSalas:
    def __init__(self) -> None:
        self.Salas: dict[str, SalaJogo] = {}

    def RestaurarSalasAtivas(self) -> None:
        _sala_persistencia.RestaurarSalasAtivas(self)

    def PersistirSala(self, Sala: SalaJogo | None) -> None:
        _sala_persistencia.PersistirSala(self, Sala)

    def MarcarConexao(self, Sala: SalaJogo, IdJogador: str, Conectado: bool) -> None:
        from . import partida_sessao

        Jogador = Sala.Jogadores.get(IdJogador)
        if not Jogador:
            return
        Jogador.Conectado = Conectado
        Jogador.UltimaAtividade = time.time()
        if Conectado:
            Jogador.AusenteContinua = False
            Jogador.DesconexaoInicioEpoch = None
            partida_sessao.RetomarPausaPorConexao(self, Sala, IdJogador)
        elif partida_sessao.PartidaEmAndamento(Sala):
            partida_sessao.IniciarPausaPorDesconexao(self, Sala, IdJogador)
        self.PersistirSala(Sala)

    def JogadoresConectados(self, Sala: SalaJogo) -> int:
        return sum(1 for J in Sala.Jogadores.values() if J.Conectado)

    def JogadoresAtivos(self, Sala: SalaJogo) -> list[JogadorSala]:
        return [J for J in Sala.Jogadores.values() if not J.Espectador]

    def JogadoresAtivosConectados(self, Sala: SalaJogo) -> int:
        return sum(1 for J in self.JogadoresAtivos(Sala) if J.Conectado)

    def EspectadoresConectados(self, Sala: SalaJogo) -> int:
        return sum(1 for J in Sala.Jogadores.values() if J.Espectador and J.Conectado)

    def EscolherNovoHost(self, Sala: SalaJogo) -> str | None:
        Candidatos = [
            J
            for J in self.JogadoresAtivos(Sala)
            if J.Conectado and J.IdJogador != Sala.CriadorId
        ]
        if not Candidatos:
            Candidatos = [J for J in self.JogadoresAtivos(Sala) if J.Conectado]
        if not Candidatos:
            return None
        return min(Candidatos, key=lambda J: J.UltimaAtividade).IdJogador

    def TransferirHostSePreciso(self, Sala: SalaJogo) -> bool:
        if Sala.CriadorId in Sala.Jogadores:
            Host = Sala.Jogadores[Sala.CriadorId]
            if Host.Conectado and not Host.Espectador:
                return False
        Novo = self.EscolherNovoHost(Sala)
        if not Novo:
            return False
        Sala.CriadorId = Novo
        return True

    def LimparJogadoresInativos(self, Sala: SalaJogo) -> bool:
        if Sala.EstadoSala == "pausada":
            return False
        Agora = time.time()
        Removidos = [
            Id
            for Id, J in Sala.Jogadores.items()
            if not J.Conectado
            and not J.AusenteContinua
            and Agora - J.UltimaAtividade > TempoInativoSegundos
        ]
        for Id in Removidos:
            self.RemoverJogador(Sala.CodigoSala, Id, Persistir=False)
        if Removidos:
            self.TransferirHostSePreciso(Sala)
            self.PersistirSala(Sala)
            return True
        return False

    def GerarCodigoSala(self) -> str:
        while True:
            Codigo = "".join(random.choices(string.ascii_uppercase, k=6))
            if Codigo not in self.Salas:
                return Codigo

    def NormalizarSenha(self, Senha: str | None) -> str | None:
        if not Senha or not Senha.strip():
            return None
        return Senha.strip()[:MaximoCaracteresSenha]

    def ValidarConfiguracao(self, Config: ConfiguracaoSala) -> str | None:
        if Config.MaximoJogadores < MinimoJogadoresSala:
            return f"Mínimo de {MinimoJogadoresSala} jogadores."
        if Config.MaximoJogadores > MaximoJogadoresPermitido:
            return f"Máximo de {MaximoJogadoresPermitido} jogadores."
        if Config.Senha and len(Config.Senha) > MaximoCaracteresSenha:
            return f"Senha deve ter no máximo {MaximoCaracteresSenha} caracteres."
        if Config.TempoLimiteSegundos < 0:
            return "Tempo limite inválido."
        if Config.TempoLimiteSegundos > 0 and (
            Config.TempoLimiteSegundos < TempoLimiteMinimoSegundos
            or Config.TempoLimiteSegundos > TempoLimiteMaximoSegundos
        ):
            return f"Tempo entre {TempoLimiteMinimoSegundos // 60} e {TempoLimiteMaximoSegundos // 60} minutos."
        if Config.NumeroRodadas < 0:
            return "Número de rodadas inválido."
        return None

    def AtivarTempoJogadores(self, Sala: SalaJogo) -> None:
        Limite = Sala.Configuracao.TempoLimiteSegundos
        if Limite <= 0:
            return
        Fim = time.time() + Limite
        for Jogador in self.JogadoresAtivos(Sala):
            Jogador.TempoFimEpoch = Fim

    def VerificarTempoEsgotado(self, Sala: SalaJogo) -> bool:
        if (
            Sala.PartidaEncerrada
            or Sala.EstadoSala != "jogando"
            or not Sala.Configuracao.TempoLimiteSegundos
        ):
            return False

        Agora = time.time()
        AlguemExpirou = False
        for Jogador in self.JogadoresAtivos(Sala):
            if Jogador.Finalizou or not Jogador.TempoFimEpoch:
                continue
            if Agora >= Jogador.TempoFimEpoch:
                Jogador.Finalizou = True
                AlguemExpirou = True
        return AlguemExpirou

    def FormatarTempoLimite(self, Segundos: int) -> str:
        if Segundos <= 0:
            return "Sem limite"
        Minutos = Segundos // 60
        Resto = Segundos % 60
        if Resto:
            return f"{Minutos} min {Resto}s"
        return f"{Minutos} min"

    def SenhaCorreta(self, Sala: SalaJogo, SenhaInformada: str | None) -> bool:
        SenhaSala = Sala.Configuracao.Senha
        if not SenhaSala:
            return True
        return (SenhaInformada or "").strip() == SenhaSala

    def CriarSala(
        self,
        NomeJogador: str,
        Configuracao: ConfiguracaoSala | None = None,
        IdConta: str | None = None,
    ) -> tuple[SalaJogo, JogadorSala]:
        Config = Configuracao or ConfiguracaoSala()
        Config.Senha = self.NormalizarSenha(Config.Senha)
        Erro = self.ValidarConfiguracao(Config)
        if Erro:
            raise ValueError(Erro)

        Codigo = self.GerarCodigoSala()
        IdJogador = str(uuid.uuid4())
        Nome = NomeJogador[:24] or "Jogador"
        from . import partida_sessao

        Jogador = JogadorSala(
            IdJogador=IdJogador,
            NomeJogador=Nome,
            IdConta=IdConta,
            TokenSessao=secrets.token_urlsafe(16),
        )
        Jogador.Conectado = True
        IdPartida = partida_sessao.GerarIdPartida()
        Sala = SalaJogo(
            CodigoSala=Codigo,
            CriadorId=IdJogador,
            Configuracao=Config,
            IdPartida=IdPartida,
            Jogadores={IdJogador: Jogador},
        )
        self.Salas[Codigo] = Sala
        persistencia.RegistrarPartidaSala(IdPartida, Codigo)
        self.PersistirSala(Sala)
        from nucleo.redis_estado import RegistrarSalaNoWorker

        RegistrarSalaNoWorker(Codigo)
        return Sala, Jogador

    def InfoConviteSala(self, CodigoSala: str) -> dict | None:
        Sala = self.ObterSala(CodigoSala.upper())
        if not Sala:
            return None
        Config = Sala.Configuracao
        Ativos = len(self.JogadoresAtivos(Sala))
        Encerrada = Sala.PartidaEncerrada or Sala.EstadoSala == "encerrada"
        Cheia = (
            not Encerrada
            and Sala.EstadoSala == "aguardando"
            and Ativos >= Config.MaximoJogadores
        )
        return {
            "codigoSala": Sala.CodigoSala,
            "temSenha": bool(Config.Senha),
            "cheia": Cheia,
            "partidaEncerrada": Encerrada,
            "estadoSala": Sala.EstadoSala,
            "jogadores": len(Sala.Jogadores),
            "jogadoresAtivos": Ativos,
            "maximoJogadores": Config.MaximoJogadores,
        }

    def EntrarSala(
        self,
        CodigoSala: str,
        NomeJogador: str,
        SenhaInformada: str | None = None,
        Espectador: bool = False,
        IdConta: str | None = None,
    ) -> tuple[SalaJogo | None, JogadorSala | None, str | None]:
        Sala = self.ObterSala(CodigoSala)
        if not Sala:
            return None, None, "Sala não encontrada."
        if Sala.PartidaEncerrada or Sala.EstadoSala == "encerrada":
            return None, None, "Partida já encerrada."
        if not self.SenhaCorreta(Sala, SenhaInformada):
            return None, None, "Senha incorreta."

        Nome = NomeJogador[:24] or "Jogador"
        if any(J.NomeJogador.lower() == Nome.lower() for J in Sala.Jogadores.values()):
            return None, None, "Este nick já está na sala."

        if Espectador:
            if Sala.EstadoSala == "aguardando":
                return None, None, "Espectadores entram após o início da partida."
            if self.EspectadoresConectados(Sala) >= MaximoEspectadores:
                return None, None, "Limite de espectadores atingido."
        else:
            if Sala.EstadoSala != "aguardando":
                return None, None, "Partida já começou. Entre como espectador."
            if len(self.JogadoresAtivos(Sala)) >= Sala.Configuracao.MaximoJogadores:
                return None, None, "Sala cheia."

        IdJogador = str(uuid.uuid4())
        from . import partida_sessao

        partida_sessao.GarantirIdPartidaSala(Sala)
        Jogador = JogadorSala(
            IdJogador=IdJogador,
            NomeJogador=Nome,
            Espectador=Espectador,
            IdConta=IdConta,
            TokenSessao=secrets.token_urlsafe(16),
        )
        Jogador.Conectado = True
        Sala.Jogadores[IdJogador] = Jogador
        self.PersistirSala(Sala)
        return Sala, Jogador, None

    def ObterSala(self, CodigoSala: str) -> SalaJogo | None:
        Codigo = CodigoSala.upper()
        if Codigo in self.Salas:
            return self.Salas[Codigo]
        Dados = persistencia.CarregarSalaSnapshot(Codigo)
        if not Dados:
            return None
        Sala = _sala_persistencia.ImportarSnapshot(Dados)
        if Sala:
            self.Salas[Codigo] = Sala
            from nucleo.redis_estado import RegistrarSalaNoWorker

            RegistrarSalaNoWorker(Codigo)
        return Sala

    def AtribuirPalavras(self, Sala: SalaJogo) -> None:
        if Sala.Configuracao.MesmaPalavra:
            Secreta, ComAcento = EscolherPalavraAleatoria()
            Sala.PalavraSecreta = Secreta
            Sala.PalavraComAcento = ComAcento
            for Jogador in self.JogadoresAtivos(Sala):
                Jogador.PalavraSecreta = Secreta
                Jogador.PalavraComAcento = ComAcento
        else:
            for Jogador in self.JogadoresAtivos(Sala):
                Secreta, ComAcento = EscolherPalavraAleatoria()
                Jogador.PalavraSecreta = Secreta
                Jogador.PalavraComAcento = ComAcento

    def JogadoresNaFilaProntidao(self, Sala: SalaJogo) -> list[JogadorSala]:
        return [
            J
            for J in self.JogadoresAtivos(Sala)
            if J.Conectado and not J.Espectador
        ]

    def ContagemProntidao(self, Sala: SalaJogo) -> tuple[int, int]:
        Lista = self.JogadoresNaFilaProntidao(Sala)
        Prontos = sum(1 for J in Lista if J.Pronto)
        return Prontos, len(Lista)

    def TodosProntos(self, Sala: SalaJogo) -> bool:
        Lista = self.JogadoresNaFilaProntidao(Sala)
        if len(Lista) < MinimoJogadoresSala:
            return False
        return all(J.Pronto for J in Lista)

    def AtualizarConfiguracaoSala(
        self,
        Sala: SalaJogo,
        IdHost: str,
        MesmaPalavra: bool,
        VerOutros: bool,
        MaximoJogadores: int,
        TempoLimiteSegundos: int,
        ModoSessao: str,
        MetaVitorias: int,
        InicioAutoDois: bool,
        SenhaNova: str | None = None,
        RemoverSenha: bool = False,
    ) -> str | None:
        if Sala.CriadorId != IdHost:
            return "Apenas o host pode alterar as configurações."
        if Sala.EstadoSala != "aguardando":
            return "Só é possível configurar na sala de espera."
        if Sala.Configuracao.Ranqueada:
            return "Duelos ranqueados não permitem alterar a configuração."

        Ocupacao = len(Sala.Jogadores)
        if MaximoJogadores < Ocupacao:
            return (
                f"Máximo de jogadores não pode ser menor que {Ocupacao} "
                "(pessoas na sala agora)."
            )

        Modo = ModoSessao if ModoSessao in (ModoPontos, ModoVitorias) else ModoPontos
        if RemoverSenha:
            Senha = None
        elif SenhaNova and str(SenhaNova).strip():
            Senha = self.NormalizarSenha(str(SenhaNova))
        else:
            Senha = Sala.Configuracao.Senha

        Config = ConfiguracaoSala(
            MesmaPalavra=bool(MesmaPalavra),
            VerOutros=bool(VerOutros),
            MaximoJogadores=int(MaximoJogadores),
            Senha=Senha,
            TempoLimiteSegundos=int(TempoLimiteSegundos),
            NumeroRodadas=Sala.Configuracao.NumeroRodadas,
            ModoSessao=Modo,
            MetaVitorias=max(1, min(20, int(MetaVitorias))),
            InicioAutoDois=bool(InicioAutoDois),
            SalaPublica=Sala.Configuracao.SalaPublica,
            Ranqueada=Sala.Configuracao.Ranqueada,
        )
        Erro = self.ValidarConfiguracao(Config)
        if Erro:
            return Erro

        Sala.Configuracao = Config
        self._ZerarProntidaoLobby(Sala)
        self.PersistirSala(Sala)
        _DispararNotificacaoLobby()
        return None

    def AlternarPronto(
        self, Sala: SalaJogo, IdJogador: str, Pronto: bool | None = None
    ) -> str | None:
        if Sala.EstadoSala != "aguardando":
            return "Só é possível marcar pronto na sala de espera."
        if IdJogador not in Sala.Jogadores:
            return "Jogador não encontrado."
        Jogador = Sala.Jogadores[IdJogador]
        if Jogador.Espectador:
            return "Espectadores não entram na fila de prontidão."
        if not Jogador.Conectado:
            return "Conecte-se à sala antes de marcar pronto."
        if Pronto is None:
            Jogador.Pronto = not Jogador.Pronto
        else:
            Jogador.Pronto = bool(Pronto)
        self.PersistirSala(Sala)
        return None

    def _ZerarProntidaoLobby(self, Sala: SalaJogo) -> None:
        for Jogador in Sala.Jogadores.values():
            Jogador.Pronto = False

    def PodeIniciar(self, Sala: SalaJogo, IdJogador: str) -> str | None:
        if Sala.CriadorId != IdJogador:
            return "Apenas quem criou a sala pode iniciar."
        if Sala.EstadoSala != "aguardando":
            return "Partida já iniciada."
        self.LimparJogadoresInativos(Sala)
        if self.JogadoresAtivosConectados(Sala) < MinimoJogadoresSala:
            return f"É preciso pelo menos {MinimoJogadoresSala} jogadores conectados."
        Prontos, Total = self.ContagemProntidao(Sala)
        if not self.TodosProntos(Sala):
            return f"Aguardando todos ficarem prontos ({Prontos}/{Total})."
        return None

    def _ResetarEstadoRodadaJogadores(self, Sala: SalaJogo) -> None:
        for Jogador in self.JogadoresAtivos(Sala):
            Jogador.Tentativas = []
            Jogador.Venceu = False
            Jogador.Finalizou = False
            Jogador.PontosUltimaRodada = 0
            Jogador.TempoFimEpoch = None
            Jogador.PalavraSecreta = None
            Jogador.PalavraComAcento = None
            if Jogador.AusenteContinua:
                Jogador.Finalizou = True

    def FinalizarAusentesRodadaAtual(self, Sala: SalaJogo) -> bool:
        if Sala.EstadoSala != "jogando":
            return False
        Mudou = False
        for Jogador in self.JogadoresAtivos(Sala):
            if Jogador.AusenteContinua and not Jogador.Finalizou:
                Jogador.Finalizou = True
                Jogador.Venceu = False
                Mudou = True
        if Mudou:
            self.PersistirSala(Sala)
        return Mudou

    def _IniciarRodadaAtiva(self, Sala: SalaJogo) -> None:
        self._ResetarEstadoRodadaJogadores(Sala)
        self.AtribuirPalavras(Sala)
        Sala.EstadoSala = "jogando"
        self.AtivarTempoJogadores(Sala)

    def IniciarPartida(self, Sala: SalaJogo, IdJogador: str) -> str | None:
        Erro = self.PodeIniciar(Sala, IdJogador)
        if Erro:
            return Erro
        Sala.RodadaAtual = 1
        self._ZerarProntidaoLobby(Sala)
        self._IniciarRodadaAtiva(Sala)
        self.PersistirSala(Sala)
        return None

    def RodadaDeveEncerrar(self, Sala: SalaJogo) -> bool:
        if Sala.EstadoSala != "jogando":
            return False
        Ativos = self.JogadoresAtivos(Sala)
        if not Ativos:
            return False
        if any(J.Venceu for J in Ativos):
            return True
        return all(J.Finalizou for J in Ativos)

    def FinalizarRodada(self, Sala: SalaJogo) -> None:
        if Sala.EstadoSala != "jogando":
            return

        Config = Sala.Configuracao
        Ativos = self.JogadoresAtivos(Sala)
        ResumoRodada = []
        IdVencedorRodada = None
        VencedoresRodadaIds: list[str] = []
        RodadaPorVerdes = False
        MaxVerdesRodada = 0
        AlgumVenceuPalavra = any(J.Venceu for J in Ativos)

        if not AlgumVenceuPalavra and Ativos:
            VencedoresRodadaIds, MaxVerdesRodada = DeterminarVencedoresRodadaPorVerdes(
                Ativos
            )
            RodadaPorVerdes = bool(VencedoresRodadaIds)

        for Jogador in Ativos:
            Tentativas = len(Jogador.Tentativas) or MaximoTentativas
            if Jogador.Venceu:
                Pontos = CalcularPontosRodada(True, Tentativas)
            elif RodadaPorVerdes and Jogador.IdJogador in VencedoresRodadaIds:
                Pontos = 1
            else:
                Pontos = 0
            Jogador.PontosUltimaRodada = Pontos
            if Config.ModoSessao == ModoPontos and Pontos > 0:
                Jogador.PontosAcumulados += Pontos
                Jogador.Pontos = Jogador.PontosAcumulados
            ResumoRodada.append(
                {
                    "idJogador": Jogador.IdJogador,
                    "nomeJogador": Jogador.NomeJogador,
                    "pontosRodada": Pontos,
                    "venceu": Jogador.Venceu,
                    "tentativas": Tentativas,
                    "verdesMelhor": MelhorContagemVerdes(Jogador),
                }
            )

        if Config.ModoSessao == ModoVitorias:
            if AlgumVenceuPalavra:
                IdVencedorRodada = DeterminarVencedorRodada(Sala)
                if IdVencedorRodada and IdVencedorRodada in Sala.Jogadores:
                    Sala.Jogadores[IdVencedorRodada].VitoriasRodada += 1
            elif RodadaPorVerdes:
                for IdV in VencedoresRodadaIds:
                    if IdV in Sala.Jogadores:
                        Sala.Jogadores[IdV].VitoriasRodada += 1
                IdVencedorRodada = (
                    VencedoresRodadaIds[0] if len(VencedoresRodadaIds) == 1 else None
                )
        Sala.UltimoVencedorRodadaId = IdVencedorRodada

        Sala.HistoricoRodadas.append(
            {
                "rodada": Sala.RodadaAtual,
                "vencedorRodadaId": IdVencedorRodada,
                "vencedoresRodadaIds": VencedoresRodadaIds,
                "empateVerdes": len(VencedoresRodadaIds) > 1,
                "porVerdes": RodadaPorVerdes,
                "maxVerdes": MaxVerdesRodada,
                "resultados": ResumoRodada,
            }
        )
        Sala.EstadoSala = "entre_rodadas"
        from .progresso import AplicarXpArenaRodadaSala

        AplicarXpArenaRodadaSala(Sala)

        if SessaoAtingiuLimite(
            Config.ModoSessao,
            Sala.RodadaAtual,
            Config.NumeroRodadas,
            Sala.Jogadores,
            Config.MetaVitorias,
        ):
            Vencedor = JogadorAtingiuMetaVitorias(Sala.Jogadores, Config.MetaVitorias)
            self.EncerrarSessao(Sala, VencedorForcado=Vencedor)

    def ProximaRodada(self, Sala: SalaJogo, IdJogador: str) -> str | None:
        if Sala.CriadorId != IdJogador:
            return "Apenas o host pode iniciar a próxima rodada."
        if Sala.EstadoSala != "entre_rodadas":
            return "Não há rodada pendente."
        if Sala.PartidaEncerrada:
            return "Sessão já encerrada."
        Config = Sala.Configuracao
        if Config.ModoSessao == ModoVitorias and JogadorAtingiuMetaVitorias(
            Sala.Jogadores, Config.MetaVitorias
        ):
            return "Alguém já venceu a sessão."
        Sala.RodadaAtual += 1
        Sala.EstadoSala = "countdown"
        Sala.CountdownFimEpoch = time.time() + SegundosCountdown
        self.PersistirSala(Sala)
        return None

    def PromoverCountdown(self, Sala: SalaJogo) -> bool:
        if Sala.EstadoSala != "countdown" or not Sala.CountdownFimEpoch:
            return False
        if time.time() < Sala.CountdownFimEpoch:
            return False
        Sala.CountdownFimEpoch = None
        self._IniciarRodadaAtiva(Sala)
        self.PersistirSala(Sala)
        return True

    def AdicionarMensagemChat(self, Sala: SalaJogo, IdJogador: str, Texto: str) -> str | None:
        Erro = AdicionarMensagemChatSala(Sala, IdJogador, Texto)
        if Erro:
            return Erro
        self.PersistirSala(Sala)
        return None

    def Revanche(self, Sala: SalaJogo, IdJogador: str) -> str | None:
        if Sala.CriadorId != IdJogador:
            return "Apenas o host pode iniciar revanche."
        if not Sala.PartidaEncerrada:
            return "Encerre a sessão atual antes da revanche."
        if self.JogadoresAtivosConectados(Sala) < MinimoJogadoresSala:
            return f"É preciso pelo menos {MinimoJogadoresSala} jogadores conectados."
        Sala.PartidaEncerrada = False
        Sala.VencedorId = None
        Sala.RodadaAtual = 0
        Sala.HistoricoRodadas = []
        Sala.MensagensChat = []
        Sala.UltimoVencedorRodadaId = None
        Sala.CountdownFimEpoch = None
        Sala.EstadoSala = "aguardando"
        self._ZerarProntidaoLobby(Sala)
        for J in self.JogadoresAtivos(Sala):
            J.PontosAcumulados = 0
            J.Pontos = 0
            J.PontosUltimaRodada = 0
            J.VitoriasRodada = 0
            J.Tentativas = []
            J.Venceu = False
            J.Finalizou = False
        self.PersistirSala(Sala)
        return None

    def TransferirHost(self, Sala: SalaJogo, IdAtual: str, IdNovo: str) -> str | None:
        if Sala.CriadorId != IdAtual:
            return "Apenas o host pode transferir."
        if IdNovo not in Sala.Jogadores:
            return "Jogador não encontrado."
        Alvo = Sala.Jogadores[IdNovo]
        if Alvo.Espectador:
            return "Espectador não pode ser host."
        if not Alvo.Conectado:
            return "Jogador precisa estar online."
        Sala.CriadorId = IdNovo
        self.PersistirSala(Sala)
        return None

    def ListarSalasPublicas(self) -> list[dict]:
        Resultado = []
        for Sala in self.Salas.values():
            Config = Sala.Configuracao
            if not Config.SalaPublica:
                continue
            if Sala.EstadoSala != "aguardando" or Sala.PartidaEncerrada:
                continue
            Ativos = len(self.JogadoresAtivos(Sala))
            Resultado.append(
                {
                    "codigoSala": Sala.CodigoSala,
                    "jogadores": Ativos,
                    "maximoJogadores": Config.MaximoJogadores,
                    "online": self.JogadoresAtivosConectados(Sala),
                    "modoSessao": Config.ModoSessao,
                    "modoSessaoTexto": FormatarModoSessao(Config.ModoSessao, Config.MetaVitorias),
                    "estadoSala": Sala.EstadoSala,
                    "temVaga": Ativos < Config.MaximoJogadores,
                    "temSenha": bool(Config.Senha),
                }
            )
        return sorted(Resultado, key=lambda I: -I["online"])[:20]

    def EncerrarSessaoCancelada(self, Sala: SalaJogo) -> None:
        """Encerra sem rodada, ranqueada, XP nem histórico (saída antes de pontuar)."""
        if Sala.PartidaEncerrada:
            return
        Sala.PartidaEncerrada = True
        Sala.PartidaCancelada = True
        Sala.EstadoSala = "encerrada"
        Sala.VencedorId = None
        if Sala.Configuracao.Ranqueada:
            from .bots_ranqueados import LiberarBotsDaSala

            LiberarBotsDaSala(Sala)
        from .sessao_jogo_conta import LimparSessaoContaJogador

        for J in Sala.Jogadores.values():
            if J.IdConta:
                LimparSessaoContaJogador(J.IdConta)
        self.PersistirSala(Sala)

    def EncerrarSessao(
        self,
        Sala: SalaJogo,
        IdJogador: str | None = None,
        VencedorForcado: str | None = None,
    ) -> str | None:
        if IdJogador and Sala.CriadorId != IdJogador:
            return "Apenas o host pode encerrar a sessão."
        if Sala.PartidaEncerrada:
            return None
        if Sala.EstadoSala == "jogando":
            self.FinalizarRodada(Sala)
            if Sala.PartidaEncerrada:
                return None
        Sala.PartidaEncerrada = True
        Sala.EstadoSala = "encerrada"
        Config = Sala.Configuracao
        Sala.VencedorId = VencedorForcado or DeterminarCampeaoSessao(
            Sala.Jogadores, Config.ModoSessao
        )
        if Config.Ranqueada:
            from .bots_ranqueados import LiberarBotsDaSala
            from .matchmaking import FilaGlobal
            from .ranqueada import ProcessarFimSalaRanqueada

            Resultados = ProcessarFimSalaRanqueada(Sala)
            LiberarBotsDaSala(Sala)
            if Resultados:
                from .progresso import RecompensaRanqueada

                for R in Resultados:
                    Jogador = next(
                        (
                            J
                            for J in Sala.Jogadores.values()
                            if J.IdConta == R.IdConta and not J.Espectador
                        ),
                        None,
                    )
                    if Jogador:
                        from .partida_sessao import JogadorSemPontuacaoNaSessao

                        if JogadorSemPontuacaoNaSessao(Jogador):
                            continue
                    RecompensaRanqueada(R.IdConta, R.Venceu)
                FilaGlobal.RegistrarFimDueloRanqueado(Sala, Resultados)
                Sala.ResultadosRanqueada = [
                    {
                        "idConta": R.IdConta,
                        "nick": R.Nick,
                        "delta": R.Delta,
                        "pontosAntes": R.PontosAntes,
                        "pontosDepois": R.PontosDepois,
                        "eloAntes": R.EloAntes,
                        "eloDepois": R.EloDepois,
                        "venceu": R.Venceu,
                    }
                    for R in Resultados
                ]
        else:
            from .progresso import AplicarXpArenaCampeaoSala

            AplicarXpArenaCampeaoSala(Sala)
        self.PersistirSala(Sala)
        return None

    def ExpulsarJogador(self, Sala: SalaJogo, IdHost: str, IdAlvo: str) -> str | None:
        if Sala.CriadorId != IdHost:
            return "Apenas o host pode expulsar."
        if IdAlvo == IdHost:
            return "O host não pode se expulsar."
        if IdAlvo not in Sala.Jogadores:
            return "Jogador não encontrado."
        if Sala.EstadoSala == "jogando" and len(self.JogadoresAtivos(Sala)) <= MinimoJogadoresSala:
            return "Não é possível expulsar com a rodada em andamento e mínimo de jogadores."
        self.RemoverJogador(Sala.CodigoSala, IdAlvo)
        return None

    def IniciarDueloRanqueado(self, Sala: SalaJogo) -> bool:
        """Matchmaking ranqueado: marca prontos e inicia sem lobby manual."""
        if not Sala.Configuracao.Ranqueada or Sala.EstadoSala != "aguardando":
            return False
        for Jogador in self.JogadoresAtivos(Sala):
            Jogador.Pronto = True
            Jogador.Conectado = True
        if self.TentarInicioAutomatico(Sala):
            return True
        Erro = self.IniciarPartida(Sala, Sala.CriadorId)
        return Erro is None

    def TentarInicioAutomatico(self, Sala: SalaJogo) -> bool:
        if Sala.EstadoSala != "aguardando":
            return False
        Config = Sala.Configuracao
        Limite = (
            Config.MaximoJogadores
            if not Config.InicioAutoDois
            else MinimoJogadoresSala
        )
        if self.JogadoresConectados(Sala) < Limite:
            return False
        if Config.InicioAutoDois and self.JogadoresAtivosConectados(Sala) < MinimoJogadoresSala:
            return False
        if not Config.InicioAutoDois and len(self.JogadoresAtivos(Sala)) < Config.MaximoJogadores:
            return False
        if not self.TodosProntos(Sala):
            return False
        Sala.RodadaAtual = 1
        self._ZerarProntidaoLobby(Sala)
        self._IniciarRodadaAtiva(Sala)
        self.PersistirSala(Sala)
        return True

    def RemoverJogador(self, CodigoSala: str, IdJogador: str, Persistir: bool = True) -> None:
        Sala = self.ObterSala(CodigoSala)
        if not Sala:
            return
        Jogador = Sala.Jogadores.get(IdJogador)
        if Jogador and Jogador.IdConta:
            from .sessao_jogo_conta import LimparSessaoContaJogador

            LimparSessaoContaJogador(Jogador.IdConta)
        Sala.Jogadores.pop(IdJogador, None)
        if not Sala.Jogadores:
            self.Salas.pop(CodigoSala.upper(), None)
            persistencia.RemoverSala(CodigoSala)
        else:
            self.TransferirHostSePreciso(Sala)
            if Persistir:
                self.PersistirSala(Sala)

    def AplicarChuteJogador(
        self,
        Sala: SalaJogo,
        IdJogador: str,
        PalavraNormalizada: str,
    ) -> bool:
        """Aplica chute validado; retorna True se alterou a sala."""
        if Sala.EstadoSala != "jogando" or Sala.PartidaEncerrada:
            return False
        Jogador = Sala.Jogadores.get(IdJogador)
        if not Jogador or Jogador.Espectador or Jogador.Finalizou:
            return False
        if self.VerificarTempoEsgotado(Sala):
            return True
        PalavraSecreta, _ = self.ObterPalavraJogador(Sala, Jogador)
        if not PalavraSecreta:
            return False
        Estados = [E.value for E in AvaliarChute(PalavraSecreta, PalavraNormalizada)]
        PalavraExibicao = (
            ObterPalavraComAcento(PalavraNormalizada) or PalavraNormalizada
        )
        Tentativa = {
            "palavra": PalavraExibicao,
            "letras": list(PalavraExibicao.upper()),
            "estados": Estados,
        }
        Jogador.Tentativas.append(Tentativa)
        Jogador.UltimaAtividade = time.time()
        if PalavraFoiAcertada(PalavraSecreta, PalavraNormalizada):
            Jogador.Venceu = True
            Jogador.Finalizou = True
        elif len(Jogador.Tentativas) >= MaximoTentativas:
            Jogador.Finalizou = True
        self.VerificarTempoEsgotado(Sala)
        if self.RodadaDeveEncerrar(Sala):
            self.FinalizarRodada(Sala)
        from .partida_sessao import GarantirIdPartidaSala, RegistrarEventoPartida

        GarantirIdPartidaSala(Sala)
        RegistrarEventoPartida(
            Sala.IdPartida,
            "chute",
            {"idJogador": IdJogador, "palavra": PalavraExibicao},
            Sala.CodigoSala,
        )
        self.PersistirSala(Sala)
        return True

    def ObterPalavraJogador(self, Sala: SalaJogo, Jogador: JogadorSala) -> tuple[str, str]:
        if Jogador.PalavraSecreta and Jogador.PalavraComAcento:
            return Jogador.PalavraSecreta, Jogador.PalavraComAcento
        if Sala.PalavraSecreta and Sala.PalavraComAcento:
            return Sala.PalavraSecreta, Sala.PalavraComAcento
        return "", ""

    @staticmethod
    def _ProgressoEventoSala(Sala: SalaJogo, IdObservador: str) -> dict | None:
        J = Sala.Jogadores.get(IdObservador)
        if not J or not J.IdConta:
            return None
        Pendentes = getattr(Sala, "PendentesXpConta", None) or {}
        Evento = Pendentes.pop(J.IdConta, None)
        return Evento

    @staticmethod
    def _RevancheRanqueadaDisponivel(Sala: SalaJogo, IdObservador: str) -> dict | None:
        if not Sala.Configuracao.Ranqueada or not Sala.PartidaEncerrada:
            return None
        J = Sala.Jogadores.get(IdObservador)
        if not J or not J.IdConta:
            return None
        from .matchmaking import FilaGlobal

        return FilaGlobal.InfoRevanche(J.IdConta)

    @staticmethod
    def ResolverAvatarJogador(Jogador: JogadorSala) -> str:
        AvatarSalvo = None
        if Jogador.IdConta:
            Conta = persistencia.ObterContaPorId(Jogador.IdConta)
            if Conta:
                AvatarSalvo = Conta.get("avatar_id")
        return ResolverAvatarId(AvatarSalvo, Jogador.NomeJogador)

    @staticmethod
    def IdJogadorPublico(Jogador: JogadorSala) -> str:
        """Oponentes bot usam id opaco — nada que revele 'bot' no cliente."""
        if not getattr(Jogador, "EhBot", False):
            return Jogador.IdJogador
        Digesto = hashlib.sha256(Jogador.IdJogador.encode()).hexdigest()
        return (
            f"{Digesto[0:8]}-{Digesto[8:12]}-{Digesto[12:16]}-"
            f"{Digesto[16:20]}-{Digesto[20:32]}"
        )

    def _SerializarOponenteRanqueado(
        self,
        Sala: SalaJogo,
        Jogador: JogadorSala,
    ) -> dict:
        EmRodada = Sala.EstadoSala == "jogando"
        JaChutou = bool(Jogador.Tentativas)
        Dados = {
            "idJogador": self.IdJogadorPublico(Jogador),
            "nomeJogador": Jogador.NomeJogador,
            "avatarId": self.ResolverAvatarJogador(Jogador),
            "souEu": False,
            "modoCompetitivo": True,
            "jaChutou": JaChutou,
            "finalizou": Jogador.Finalizou,
            "conectado": Jogador.Conectado,
            "espectador": Jogador.Espectador,
            "pronto": Jogador.Pronto,
            "ausenteContinua": Jogador.AusenteContinua,
            "tentativas": [],
            "tentativasUsadas": 0,
            "pontos": 0,
            "pontosAcumulados": 0,
            "pontosUltimaRodada": 0,
            "vitoriasRodada": 0,
            "venceu": Jogador.Venceu if not EmRodada else False,
        }
        if Jogador.AusenteContinua and Jogador.DesconexaoInicioEpoch:
            from . import partida_sessao

            Dados["segundosAteAbandono"] = max(
                0,
                int(
                    partida_sessao.ABANDONO_TOTAL_SEG
                    - (time.time() - Jogador.DesconexaoInicioEpoch)
                ),
            )
        return Dados

    def SerializarJogador(
        self,
        Sala: SalaJogo,
        Jogador: JogadorSala,
        IdObservador: str,
        IncluirTentativas: bool,
    ) -> dict:
        from . import partida_sessao

        SouEu = Jogador.IdJogador == IdObservador
        if Sala.Configuracao.Ranqueada and not SouEu and not Jogador.Espectador:
            return self._SerializarOponenteRanqueado(Sala, Jogador)
        Dados = {
            "idJogador": self.IdJogadorPublico(Jogador),
            "nomeJogador": Jogador.NomeJogador,
            "avatarId": self.ResolverAvatarJogador(Jogador),
            "venceu": Jogador.Venceu,
            "finalizou": Jogador.Finalizou,
            "pontos": Jogador.PontosAcumulados,
            "pontosAcumulados": Jogador.PontosAcumulados,
            "pontosUltimaRodada": Jogador.PontosUltimaRodada,
            "vitoriasRodada": Jogador.VitoriasRodada,
            "souEu": SouEu,
            "tentativasUsadas": len(Jogador.Tentativas),
            "conectado": Jogador.Conectado,
            "espectador": Jogador.Espectador,
            "pronto": Jogador.Pronto,
            "ausenteContinua": Jogador.AusenteContinua,
        }
        if Jogador.AusenteContinua and Jogador.DesconexaoInicioEpoch:
            RestanteKick = max(
                0,
                int(
                    partida_sessao.ABANDONO_TOTAL_SEG
                    - (time.time() - Jogador.DesconexaoInicioEpoch)
                ),
            )
            Dados["segundosAteAbandono"] = RestanteKick
        if IncluirTentativas or SouEu:
            Dados["tentativas"] = Jogador.Tentativas
        else:
            Dados["tentativas"] = []
        if Sala.PartidaEncerrada and SouEu:
            _, ComAcento = self.ObterPalavraJogador(Sala, Jogador)
            Dados["minhaPalavraRevelada"] = ComAcento
        if Jogador.TempoFimEpoch and not Jogador.Finalizou:
            Dados["segundosRestantes"] = max(0, int(Jogador.TempoFimEpoch - time.time()))
        elif Jogador.Finalizou and Jogador.TempoFimEpoch and not Jogador.Venceu:
            Dados["tempoEsgotado"] = True
        if SouEu and Jogador.TempoFimEpoch:
            Dados["tempoFimEpoch"] = Jogador.TempoFimEpoch
        if not Jogador.Espectador:
            from .ranqueada import MetadadosRankJogadorSala

            Dados.update(MetadadosRankJogadorSala(Jogador))
        return Dados

    def EstadoPublicoSala(self, Sala: SalaJogo, IdObservador: str) -> dict:
        from . import partida_sessao

        partida_sessao.GarantirIdPartidaSala(Sala)
        VerOutros = Sala.Configuracao.VerOutros
        Config = Sala.Configuracao
        JogadoresPlacar = {
            K: V for K, V in Sala.Jogadores.items() if not V.Espectador
        }
        Placar = MontarPlacar(
            JogadoresPlacar,
            Config.ModoSessao,
            Config.MetaVitorias,
        )
        for Linha in Placar:
            J = JogadoresPlacar.get(Linha["idJogador"])
            if J:
                Linha["avatarId"] = self.ResolverAvatarJogador(J)
                from .ranqueada import MetadadosRankJogadorSala

                Linha.update(MetadadosRankJogadorSala(J))
        NumeroRodadas = Config.NumeroRodadas
        Maratona = Config.ModoSessao == ModoPontos
        UltimoNome = None
        if Sala.UltimoVencedorRodadaId and Sala.UltimoVencedorRodadaId in Sala.Jogadores:
            UltimoNome = Sala.Jogadores[Sala.UltimoVencedorRodadaId].NomeJogador
        UltimaRodada = (
            Sala.HistoricoRodadas[-1]
            if Sala.HistoricoRodadas
            and Sala.EstadoSala in ("entre_rodadas", "countdown")
            else {}
        )
        MensagemFimRodada = None
        if UltimaRodada:
            MensagemFimRodada = MontarMensagemFimRodada(
                Sala.HistoricoRodadas,
                IdObservador,
                Sala.Jogadores,
            )
        VencedoresRodadaIds = UltimaRodada.get("vencedoresRodadaIds") or []
        VencedoresRodadaNomes = [
            Sala.Jogadores[I].NomeJogador
            for I in VencedoresRodadaIds
            if I in Sala.Jogadores
        ]
        CountdownSeg = None
        if Sala.CountdownFimEpoch:
            CountdownSeg = max(0, int(Sala.CountdownFimEpoch - time.time()))
        Prontos, TotalProntidao = self.ContagemProntidao(Sala)
        ErroIniciar = (
            self.PodeIniciar(Sala, IdObservador)
            if Sala.CriadorId == IdObservador
            else None
        )
        Eu = Sala.Jogadores.get(IdObservador)
        RespostaBase = {
            "idPartida": Sala.IdPartida,
            "codigoSala": Sala.CodigoSala,
            "estadoSala": Sala.EstadoSala,
            "partidaEncerrada": Sala.PartidaEncerrada,
            "partidaCancelada": getattr(Sala, "PartidaCancelada", False),
            "vencedorId": Sala.VencedorId,
            "criadorId": Sala.CriadorId,
            "souCriador": Sala.CriadorId == IdObservador,
            "maximoTentativas": MaximoTentativas,
            "temSenha": bool(Config.Senha),
            "rodadaAtual": Sala.RodadaAtual,
            "totalRodadas": NumeroRodadas,
            "modoSessao": Config.ModoSessao,
            "metaVitorias": Config.MetaVitorias,
            "modoSessaoTexto": FormatarModoSessao(
                Config.ModoSessao, Config.MetaVitorias, Config.Ranqueada
            ),
            "modoRodadasTexto": FormatarModoSessao(
                Config.ModoSessao, Config.MetaVitorias, Config.Ranqueada
            ),
            "rodadasRestantes": None,
            "maratona": Maratona,
            "ranqueada": Config.Ranqueada,
            "placar": Placar,
            "resultadosRanqueada": Sala.ResultadosRanqueada,
            "podeProximaRodada": (
                Sala.CriadorId == IdObservador
                and Sala.EstadoSala == "entre_rodadas"
                and not Sala.PartidaEncerrada
                and not SessaoAtingiuLimite(
                    Config.ModoSessao,
                    Sala.RodadaAtual,
                    NumeroRodadas,
                    Sala.Jogadores,
                    Config.MetaVitorias,
                )
            ),
            "podeEncerrarSessao": Sala.CriadorId == IdObservador and not Sala.PartidaEncerrada,
            "podeRevanche": Sala.CriadorId == IdObservador and Sala.PartidaEncerrada,
            "mensagensChat": Sala.MensagensChat[-MaximoMensagensChat:],
            "countdownSegundos": CountdownSeg,
            "ultimoVencedorRodada": UltimoNome,
            "ultimoVencedorRodadaId": Sala.UltimoVencedorRodadaId,
            "rodadaPorVerdes": UltimaRodada.get("porVerdes", False),
            "empateVerdesRodada": UltimaRodada.get("empateVerdes", False),
            "vencedoresRodadaIds": VencedoresRodadaIds,
            "vencedoresRodadaNomes": VencedoresRodadaNomes,
            "maxVerdesRodada": UltimaRodada.get("maxVerdes", 0),
            "mensagemFimRodada": MensagemFimRodada,
            "progressoEvento": self._ProgressoEventoSala(Sala, IdObservador),
            "revancheRanqueada": self._RevancheRanqueadaDisponivel(Sala, IdObservador),
            "configuracao": {
                "mesmaPalavra": Config.MesmaPalavra,
                "verOutros": Config.VerOutros,
                "maximoJogadores": Config.MaximoJogadores,
                "tempoLimiteSegundos": Config.TempoLimiteSegundos,
                "tempoLimiteTexto": self.FormatarTempoLimite(Config.TempoLimiteSegundos),
                "numeroRodadas": NumeroRodadas,
                "modoSessao": Config.ModoSessao,
                "metaVitorias": Config.MetaVitorias,
                "modoSessaoTexto": FormatarModoSessao(
                    Config.ModoSessao, Config.MetaVitorias, Config.Ranqueada
                ),
                "modoRodadasTexto": FormatarModoSessao(
                    Config.ModoSessao, Config.MetaVitorias, Config.Ranqueada
                ),
                "inicioAutoDois": Config.InicioAutoDois,
                "salaPublica": Config.SalaPublica,
                "ranqueada": Config.Ranqueada,
                "ehDesafio": Config.EhDesafio,
            },
            "jogadoresConectados": len(self.JogadoresAtivos(Sala)),
            "jogadoresOnline": self.JogadoresAtivosConectados(Sala),
            "espectadoresOnline": self.EspectadoresConectados(Sala),
            "prontosOnline": Prontos,
            "totalProntidao": TotalProntidao,
            "todosProntos": self.TodosProntos(Sala),
            "podeIniciar": ErroIniciar is None and Sala.CriadorId == IdObservador,
            "motivoNaoIniciar": ErroIniciar,
            "palavraRevelada": (
                Sala.PalavraComAcento
                if Sala.PartidaEncerrada and Config.MesmaPalavra
                else (
                    Sala.PalavraComAcento
                    if Sala.EstadoSala == "entre_rodadas" and Config.MesmaPalavra
                    else None
                )
            ),
            "jogadores": [
                self.SerializarJogador(
                    Sala,
                    J,
                    IdObservador,
                    VerOutros or J.IdJogador == IdObservador,
                )
                for J in Sala.Jogadores.values()
            ],
        }
        RespostaBase.update(partida_sessao.CamposPausaPublicos(Sala))
        if Eu and getattr(Eu, "TokenSessao", None):
            RespostaBase["tokenSessao"] = Eu.TokenSessao
        return RespostaBase

    def DeterminarVencedor(self, Sala: SalaJogo) -> str | None:
        Vencedores = [J for J in Sala.Jogadores.values() if J.Venceu]
        if not Vencedores:
            return None
        if len(Vencedores) == 1:
            return Vencedores[0].IdJogador
        return min(Vencedores, key=lambda J: len(J.Tentativas)).IdJogador

    def TodosFinalizaram(self, Sala: SalaJogo) -> bool:
        Ativos = self.JogadoresAtivos(Sala)
        return bool(Ativos) and all(J.Finalizou for J in Ativos)
