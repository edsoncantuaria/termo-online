"""Fila de matchmaking ranqueado (1v1) com bots após busca por jogador real."""

import time
from dataclasses import dataclass, field

from .arena_rodadas import ModoVitorias
from .bots_ranqueados import (
    BotsRanqueadosAtivos,
    ContarBotsDisponiveis,
    EscolherBotParaPontos,
    LiberarReservaBot,
    ListarBotsProximos,
    MarcarBotEmPartida,
    ObterBot,
    PontosBotAtual,
    ReservarBot,
)
from .contas import ExigirPodeRanquear
from .gerenciador_salas import ConfiguracaoSala, GerenciadorSalas, JogadorSala
from .matchmaking_competitivo import (
    BUSCA_REAL_SEG,
    ESPERA_BOT_SEG,
    JanelaRpPermitida,
    PodeParearRp,
    ResumoJanelaCliente,
    ScoreQualidadePar,
    SegundosNaFila,
)
from .controle_carga import ContarConexoesWsLobby, ContarConexoesWsSala
from .persistencia import ContarPartidasRanqueadasConta
from .ranqueada import EloDePontos, NomeEloExibicao

MIN_JOGADORES_ONLINE_EXIBIR = 50


@dataclass
class EntradaFila:
    IdConta: str
    Nick: str
    Pontos: int
    EntrouEm: float = field(default_factory=time.time)
    BotReservadoId: str | None = None
    Treino: bool = False


def JogadoresOnlineParaCliente() -> int | None:
    """Só exibe contagem pública quando há massa crítica de jogadores reais (WS)."""
    Total = ContarConexoesWsLobby() + ContarConexoesWsSala()
    if Total < MIN_JOGADORES_ONLINE_EXIBIR:
        return None
    return Total


class FilaMatchmaking:
    def __init__(self) -> None:
        self.Fila: dict[str, EntradaFila] = {}
        self.UltimoMatch: dict[str, dict] = {}
        self.UltimoOponenteHumano: dict[str, dict] = {}
        self.RevancheAlvo: dict[str, str] = {}

    def _SalvarEntradaFila(self, IdConta: str, E: EntradaFila) -> None:
        """Persiste alterações (obrigatório com fila Redis — get desserializa cópia)."""
        if IdConta in self.Fila:
            self.Fila[IdConta] = E

    def _ProcessarBotsNaFila(self, Gerenciador: GerenciadorSalas) -> None:
        """Reserva e inicia duelo contra bot — não exige lock Redis (pareamento PvP sim)."""
        if not BotsRanqueadosAtivos():
            return
        Agora = time.time()
        for IdConta in list(self.Fila.keys()):
            E = self.Fila.get(IdConta)
            if not E:
                continue
            Seg = Agora - E.EntrouEm
            Alterou = False
            if Seg >= BUSCA_REAL_SEG and not E.BotReservadoId:
                Bot = EscolherBotParaPontos(E.Pontos, Seg)
                if Bot:
                    ReservarBot(Bot.Id)
                    E.BotReservadoId = Bot.Id
                    Alterou = True
            if Seg < BUSCA_REAL_SEG + ESPERA_BOT_SEG:
                if Alterou:
                    self._SalvarEntradaFila(IdConta, E)
                continue
            Bot = None
            if E.BotReservadoId:
                Bot = ObterBot(E.BotReservadoId)
            if not Bot:
                Bot = EscolherBotParaPontos(E.Pontos, Seg)
            if not Bot:
                if Alterou:
                    self._SalvarEntradaFila(IdConta, E)
                continue
            Entrada = self.Fila.pop(IdConta, None)
            if not Entrada:
                continue
            try:
                self._CriarDueloComBot(Gerenciador, Entrada, Bot)
            except Exception:
                if Entrada.BotReservadoId:
                    LiberarReservaBot(Entrada.BotReservadoId)
                LiberarReservaBot(Bot.Id)
                self.Fila[IdConta] = Entrada
                raise

    def Processar(self, Gerenciador: GerenciadorSalas) -> None:
        self._ProcessarBotsNaFila(Gerenciador)
        self._TentarParearReais(Gerenciador)

    def Status(self, IdConta: str, Gerenciador: GerenciadorSalas | None = None) -> dict:
        if Gerenciador:
            self.Processar(Gerenciador)
        if IdConta in self.UltimoMatch:
            M = self.UltimoMatch.pop(IdConta, None)
            if M:
                return {"estado": "encontrado", **M}
        if IdConta not in self.Fila:
            return {"estado": "idle"}

        E = self.Fila[IdConta]
        Seg = int(time.time() - E.EntrouEm)
        ReaisNaFila = len(self.Fila)
        Fase, Mensagem = self._FaseEMensagem(E, Seg)
        Preview = self._MontarPreview(E)

        FaseCliente = self._FaseCliente(Fase)
        Agora = time.time()
        Busca = ResumoJanelaCliente(E.Pontos, SegundosNaFila(E.EntrouEm, Agora))
        return {
            "estado": "aguardando",
            "segundos": Seg,
            "jogadoresNaFila": ReaisNaFila,
            "jogadoresOnline": JogadoresOnlineParaCliente(),
            "fase": FaseCliente,
            "mensagem": Mensagem,
            "filaPreview": Preview,
            "busca": Busca,
        }

    @staticmethod
    def _FaseCliente(FaseInterna: str) -> str:
        if FaseInterna in ("busca_real", "acordando_bot"):
            return "busca"
        if FaseInterna == "aguardando_real":
            return "encontrando"
        return "entrando"

    def _FaseEMensagem(self, E: EntradaFila, Seg: int) -> tuple[str, str]:
        if Seg < BUSCA_REAL_SEG:
            J = JanelaRpPermitida(E.Pontos, Seg)
            return (
                "busca_real",
                f"Procurando oponente entre {max(0, E.Pontos - J)} e {E.Pontos + J} RP…",
            )
        if Seg < BUSCA_REAL_SEG + ESPERA_BOT_SEG:
            if E.BotReservadoId:
                Bot = ObterBot(E.BotReservadoId)
                Nome = Bot.Nick if Bot else "Um jogador"
                Resto = BUSCA_REAL_SEG + ESPERA_BOT_SEG - Seg
                return (
                    "aguardando_real",
                    f"{Nome} também está na fila — confirmando partida ({Resto}s)…",
                )
            return (
                "acordando_bot",
                "Ampliando busca entre jogadores online…",
            )
        return ("entrando", "Iniciando duelo…")

    @staticmethod
    def _ItemPreview(
        Nick: str, Pontos: int, *, naFila: bool, destacado: bool = False
    ) -> dict:
        Elo = EloDePontos(Pontos)
        return {
            "nick": Nick,
            "pontos": Pontos,
            "elo": Elo,
            "eloNome": NomeEloExibicao(Elo),
            "naFila": naFila,
            "destacado": destacado,
        }

    def _MontarPreview(self, Eu: EntradaFila) -> list[dict]:
        Itens: list[dict] = []
        if Eu.BotReservadoId:
            Bot = ObterBot(Eu.BotReservadoId)
            if Bot:
                Itens.append(
                    self._ItemPreview(
                        Bot.Nick, PontosBotAtual(Bot.Id), naFila=True, destacado=False
                    )
                )
        for Outro in self.Fila.values():
            if Outro.IdConta == Eu.IdConta:
                continue
            Itens.append(self._ItemPreview(Outro.Nick, Outro.Pontos, naFila=True))
        Vistos = {I["nick"] for I in Itens}
        for Bot in ListarBotsProximos(Eu.Pontos, 12):
            if Bot.Nick in Vistos:
                continue
            Itens.append(
                self._ItemPreview(Bot.Nick, PontosBotAtual(Bot.Id), naFila=True)
            )
            Vistos.add(Bot.Nick)
        return Itens[:14]

    def Sair(self, IdConta: str) -> None:
        E = self.Fila.pop(IdConta, None)
        self.RevancheAlvo.pop(IdConta, None)
        if E and E.BotReservadoId:
            LiberarReservaBot(E.BotReservadoId)

    def Entrar(
        self, Perfil: dict, Gerenciador: GerenciadorSalas, *, Treino: bool = False
    ) -> dict:
        from .controle_carga import PodeEntrarFilaRanqueada

        ExigirPodeRanquear(Perfil)
        IdConta = Perfil["idConta"]
        Admissao = PodeEntrarFilaRanqueada(len(self.Fila), IdConta in self.Fila)
        if not Admissao.Permitido:
            return {
                "estado": "fila_cheia",
                "mensagem": Admissao.Mensagem,
                "posicaoFila": Admissao.PosicaoFila,
                "retryAfterSegundos": Admissao.RetryAfterSegundos,
            }
        self.Sair(IdConta)
        self.RevancheAlvo.pop(IdConta, None)
        self.Fila[IdConta] = EntradaFila(
            IdConta=IdConta,
            Nick=Perfil["nick"],
            Pontos=int(Perfil["pontosRanqueada"]),
            Treino=bool(Treino),
        )
        self.Processar(Gerenciador)
        return self.Status(IdConta, Gerenciador)

    def RegistrarFimDueloRanqueado(self, Sala, Resultados) -> None:
        PorConta = {
            R.IdConta: R
            for R in Resultados
            if R.IdConta
            and any(
                J.IdConta == R.IdConta and not getattr(J, "EhBot", False)
                for J in Sala.Jogadores.values()
            )
        }
        Ids = list(PorConta.keys())
        if len(Ids) != 2:
            return
        IdA, IdB = Ids[0], Ids[1]
        Ra, Rb = PorConta[IdA], PorConta[IdB]
        self.UltimoOponenteHumano[IdA] = {
            "idConta": IdB,
            "nick": Rb.Nick,
            "pontos": Rb.PontosDepois,
        }
        self.UltimoOponenteHumano[IdB] = {
            "idConta": IdA,
            "nick": Ra.Nick,
            "pontos": Ra.PontosDepois,
        }

    def InfoRevanche(self, IdConta: str) -> dict | None:
        O = self.UltimoOponenteHumano.get(IdConta)
        if not O:
            return None
        return {
            "disponivel": True,
            "oponenteNick": O["nick"],
            "oponenteIdConta": O["idConta"],
            "aguardandoOponente": self.RevancheAlvo.get(O["idConta"]) != IdConta,
        }

    def SolicitarRevanche(self, IdConta: str, Gerenciador: GerenciadorSalas) -> dict:
        O = self.UltimoOponenteHumano.get(IdConta)
        if not O:
            return {"ok": False, "mensagem": "Nenhum duelo recente contra jogador real."}
        self.RevancheAlvo[IdConta] = O["idConta"]
        self.Processar(Gerenciador)
        return {
            "ok": True,
            "mensagem": f"Procurando revanche com {O['nick']}…",
            "oponenteNick": O["nick"],
        }

    def _TentarParearRevanche(self, Gerenciador: GerenciadorSalas) -> None:
        Pares: list[tuple[EntradaFila, EntradaFila]] = []
        for IdA, AlvoId in list(self.RevancheAlvo.items()):
            if IdA not in self.Fila or AlvoId not in self.Fila:
                continue
            if self.RevancheAlvo.get(AlvoId) != IdA:
                continue
            Pares.append((self.Fila[IdA], self.Fila[AlvoId]))
        for A, B in Pares:
            if A.BotReservadoId:
                LiberarReservaBot(A.BotReservadoId)
            if B.BotReservadoId:
                LiberarReservaBot(B.BotReservadoId)
            self._CriarDuelo(Gerenciador, A, B)
            self.Fila.pop(A.IdConta, None)
            self.Fila.pop(B.IdConta, None)
            self.RevancheAlvo.pop(A.IdConta, None)
            self.RevancheAlvo.pop(B.IdConta, None)

    def _TentarParearReais(self, Gerenciador: GerenciadorSalas) -> None:
        self._TentarParearRevanche(Gerenciador)
        if len(self.Fila) < 2:
            return
        Agora = time.time()
        Entradas = [
            E for E in self.Fila.values() if E.IdConta not in self.RevancheAlvo
        ]
        Candidatos: list[tuple[int, EntradaFila, EntradaFila]] = []

        for i, A in enumerate(Entradas):
            Sa = SegundosNaFila(A.EntrouEm, Agora)
            for B in Entradas[i + 1 :]:
                Sb = SegundosNaFila(B.EntrouEm, Agora)
                Pa = ContarPartidasRanqueadasConta(A.IdConta)
                Pb = ContarPartidasRanqueadasConta(B.IdConta)
                if A.Treino != B.Treino:
                    continue
                if not PodeParearRp(
                    A.Pontos, Sa, B.Pontos, Sb, PartidasA=Pa, PartidasB=Pb
                ):
                    continue
                Candidatos.append(
                    (ScoreQualidadePar(A.Pontos, Sa, B.Pontos, Sb), A, B)
                )

        Candidatos.sort(key=lambda T: T[0])
        Usados: set[str] = set()

        for _, A, Par in Candidatos:
            if A.IdConta in Usados or Par.IdConta in Usados:
                continue
            Usados.add(A.IdConta)
            Usados.add(Par.IdConta)
            if A.BotReservadoId:
                LiberarReservaBot(A.BotReservadoId)
            if Par.BotReservadoId:
                LiberarReservaBot(Par.BotReservadoId)
            self._CriarDuelo(Gerenciador, A, Par)

        for Id in Usados:
            self.Fila.pop(Id, None)

    def _CriarDuelo(
        self,
        Gerenciador: GerenciadorSalas,
        A: EntradaFila,
        B: EntradaFila,
    ) -> None:
        Config = self._ConfigRanqueada(A.Treino)
        Sala, J1 = Gerenciador.CriarSala(A.Nick, Config, IdConta=A.IdConta)
        _Sala2, J2, Erro = Gerenciador.EntrarSala(
            Sala.CodigoSala,
            B.Nick,
            None,
            False,
            IdConta=B.IdConta,
        )
        if Erro or not J2:
            return
        Gerenciador.IniciarDueloRanqueado(Sala)
        Sala = Gerenciador.ObterSala(Sala.CodigoSala) or Sala
        Gerenciador.PersistirSala(Sala)
        self._RegistrarMatch(A, B, Sala, J1, J2, oponente_eh_bot=False)

    def _CriarDueloComBot(
        self,
        Gerenciador: GerenciadorSalas,
        A: EntradaFila,
        Bot,
    ) -> None:
        Config = self._ConfigRanqueada(A.Treino)
        Sala, J1 = Gerenciador.CriarSala(A.Nick, Config, IdConta=A.IdConta)
        IdBotJogador = f"bot-{Bot.Id}"
        J2 = JogadorSala(
            IdJogador=IdBotJogador,
            NomeJogador=Bot.Nick,
            EhBot=True,
            Conectado=True,
        )
        Sala.Jogadores[IdBotJogador] = J2
        MarcarBotEmPartida(Bot.Id)
        J2.Pronto = True
        Gerenciador.IniciarDueloRanqueado(Sala)
        Sala = Gerenciador.ObterSala(Sala.CodigoSala) or Sala
        Gerenciador.PersistirSala(Sala)
        self._RegistrarMatch(
            A,
            None,
            Sala,
            J1,
            J2,
            oponente_eh_bot=True,
            nick_bot=Bot.Nick,
        )

    def _ConfigRanqueada(self, Treino: bool = False) -> ConfiguracaoSala:
        return ConfiguracaoSala(
            MesmaPalavra=True,
            VerOutros=False,
            MaximoJogadores=2,
            Senha=None,
            TempoLimiteSegundos=204,
            NumeroRodadas=3,
            ModoSessao=ModoVitorias,
            MetaVitorias=2,
            InicioAutoDois=True,
            SalaPublica=False,
            Ranqueada=True,
            TreinoRanqueado=bool(Treino),
        )

    def _RegistrarMatch(
        self,
        A: EntradaFila,
        B: EntradaFila | None,
        Sala,
        J1,
        J2,
        *,
        oponente_eh_bot: bool,
        nick_bot: str | None = None,
    ) -> None:
        IdPartida = getattr(Sala, "IdPartida", None)
        if B:
            for Entrada, Jogador in ((A, J1), (B, J2)):
                self.UltimoMatch[Entrada.IdConta] = {
                    "codigoSala": Sala.CodigoSala,
                    "idPartida": IdPartida,
                    "idJogador": Jogador.IdJogador,
                    "tokenSessao": getattr(Jogador, "TokenSessao", None),
                    "nickOponente": B.Nick if Entrada.IdConta == A.IdConta else A.Nick,
                }
        else:
            self.UltimoMatch[A.IdConta] = {
                "codigoSala": Sala.CodigoSala,
                "idPartida": IdPartida,
                "idJogador": J1.IdJogador,
                "tokenSessao": getattr(J1, "TokenSessao", None),
                "nickOponente": nick_bot or "Jogador",
            }


def _InicializarFilaGlobal() -> FilaMatchmaking:
    from .redis_fila import ConstruirFilaGlobal

    return ConstruirFilaGlobal()


FilaGlobal = _InicializarFilaGlobal()
