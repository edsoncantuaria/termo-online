import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from nucleo.logica_jogo import ValidarPalavra
from nucleo.pontuacao import RegistrarPontuacao
from servidor.estado_global import GerenciadorVersus as Gerenciador

ConexoesPorSala: dict[str, dict[str, WebSocket]] = {}
ConexoesLobby: set[WebSocket] = set()
_TarefaBroadcastLobby: asyncio.Task | None = None


def AgendarAtualizacaoLobbySalas() -> None:
    """Dispara broadcast das salas públicas (debounce ~150ms)."""
    global _TarefaBroadcastLobby
    try:
        Loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    if _TarefaBroadcastLobby and not _TarefaBroadcastLobby.done():
        _TarefaBroadcastLobby.cancel()

    async def _Executar():
        await asyncio.sleep(0.15)
        await BroadcastSalasPublicasLobby()

    _TarefaBroadcastLobby = Loop.create_task(_Executar())


async def BroadcastSalasPublicasLobby() -> None:
    from servidor.estado_global import GerenciadorVersus

    GerenciadorVersus.RestaurarSalasAtivas()
    Payload = {
        "tipo": "salasPublicas",
        "salas": GerenciadorVersus.ListarSalasPublicas(),
    }
    Mortas: list[WebSocket] = []
    for Conexao in list(ConexoesLobby):
        try:
            await Conexao.send_json(Payload)
        except Exception:
            Mortas.append(Conexao)
    for Conexao in Mortas:
        ConexoesLobby.discard(Conexao)


async def ConectarWebSocketLobby(Conexao: WebSocket) -> None:
    from nucleo.controle_carga import PodeAceitarWsLobby, RegistrarConexaoWsLobby, LiberarConexaoWsLobby

    Admissao = PodeAceitarWsLobby()
    if not Admissao.Permitido:
        await Conexao.close(code=1013, reason=Admissao.Mensagem or "Servidor cheio")
        return
    await Conexao.accept()
    RegistrarConexaoWsLobby()
    ConexoesLobby.add(Conexao)
    try:
        from servidor.estado_global import GerenciadorVersus

        GerenciadorVersus.RestaurarSalasAtivas()
        await Conexao.send_json(
            {
                "tipo": "salasPublicas",
                "salas": GerenciadorVersus.ListarSalasPublicas(),
            }
        )
        while True:
            await Conexao.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        from nucleo.controle_carga import LiberarConexaoWsLobby

        ConexoesLobby.discard(Conexao)
        LiberarConexaoWsLobby()


async def EnviarParaJogador(CodigoSala: str, IdJogador: str, Mensagem: dict) -> bool:
    Conexao = ConexoesPorSala.get(CodigoSala, {}).get(IdJogador)
    if not Conexao:
        return False
    try:
        await Conexao.send_json(Mensagem)
        return True
    except Exception:
        RemoverConexao(CodigoSala, IdJogador)
        return False


def RegistrarConexao(CodigoSala: str, IdJogador: str, Conexao: WebSocket) -> None:
    ConexoesPorSala.setdefault(CodigoSala, {})[IdJogador] = Conexao


def RemoverConexao(CodigoSala: str, IdJogador: str) -> None:
    Conexoes = ConexoesPorSala.get(CodigoSala, {})
    Conexoes.pop(IdJogador, None)
    if not Conexoes:
        ConexoesPorSala.pop(CodigoSala, None)


async def BroadcastEstadoSala(Sala) -> None:
    if not Sala:
        return
    Codigo = Sala.CodigoSala
    SalaAtual = Gerenciador.ObterSala(Codigo) or Sala
    for IdJogador in list(SalaAtual.Jogadores.keys()):
        await EnviarParaJogador(
            Codigo,
            IdJogador,
            {
                "tipo": "estadoSala",
                "dados": Gerenciador.EstadoPublicoSala(SalaAtual, IdJogador),
            },
        )
    AgendarAtualizacaoLobbySalas()


def RegistrarRankingSessao(Sala) -> None:
    if getattr(Sala.Configuracao, "Ranqueada", False):
        return
    from nucleo import persistencia

    for Jogador in Sala.Jogadores.values():
        if getattr(Jogador, "Espectador", False) or getattr(Jogador, "EhBot", False):
            continue
        if Jogador.PontosAcumulados <= 0:
            continue
        IdConta = getattr(Jogador, "IdConta", None)
        if IdConta:
            Conta = persistencia.ObterContaPorId(IdConta)
            if not Conta or Conta.get("eh_visitante"):
                continue
        elif persistencia.NickEhVisitante(Jogador.NomeJogador):
            continue
        RegistrarPontuacao(
            Jogador.NomeJogador,
            Jogador.PontosAcumulados,
            "sala",
            max(1, Jogador.VitoriasRodada),
            Jogador.IdJogador == Sala.VencedorId,
            IdConta=IdConta,
        )


def VerificarFimRodada(Sala) -> None:
    if not Gerenciador.RodadaDeveEncerrar(Sala):
        return
    Gerenciador.FinalizarRodada(Sala)
    if Sala.PartidaEncerrada:
        RegistrarRankingSessao(Sala)


async def _AvisarJogadorSala(Sala, IdJogador: str, Tipo: str, Mensagem: str) -> None:
    await EnviarParaJogador(
        Sala.CodigoSala,
        IdJogador,
        {"tipo": Tipo, "mensagem": Mensagem},
    )


async def ProcessarChuteSala(Sala, IdJogador: str, Palavra: str) -> dict:
    """Processa chute na arena/ranqueada. Retorno usado pelo fallback HTTP."""
    if Sala.EstadoSala != "jogando":
        Msg = "Nenhuma rodada em andamento."
        await _AvisarJogadorSala(Sala, IdJogador, "erro", Msg)
        return {"valido": False, "mensagem": Msg}

    if Sala.PartidaEncerrada:
        Msg = "Sessão já encerrada."
        await _AvisarJogadorSala(Sala, IdJogador, "erro", Msg)
        return {"valido": False, "mensagem": Msg}

    Jogador = Sala.Jogadores.get(IdJogador)
    if not Jogador:
        return {"valido": False, "mensagem": "Jogador não encontrado na sala."}

    from nucleo.redis_estado import PermitirRequisicaoRateLimit

    ChaveRl = f"chute:{Jogador.IdConta or IdJogador}:{getattr(Sala, 'IdPartida', Sala.CodigoSala)}"
    if not PermitirRequisicaoRateLimit(ChaveRl, 40, 60):
        Msg = "Muitos chutes em pouco tempo — aguarde um instante."
        await _AvisarJogadorSala(Sala, IdJogador, "erro", Msg)
        return {"valido": False, "mensagem": Msg}

    if Jogador.Espectador:
        Msg = "Espectadores não podem chutar."
        await _AvisarJogadorSala(Sala, IdJogador, "erro", Msg)
        return {"valido": False, "mensagem": Msg}

    if Jogador.Finalizou:
        Mensagem = (
            "Tempo esgotado."
            if Jogador.TempoFimEpoch and not Jogador.Venceu
            else "Você já finalizou esta rodada."
        )
        await _AvisarJogadorSala(Sala, IdJogador, "erro", Mensagem)
        return {"valido": False, "mensagem": Mensagem}

    if Gerenciador.VerificarTempoEsgotado(Sala):
        VerificarFimRodada(Sala)
        await BroadcastEstadoSala(Sala)
        Estado = Gerenciador.EstadoPublicoSala(Sala, IdJogador)
        return {"valido": True, "estado": Estado, "tempoEsgotado": True}

    Valido, MensagemOuPalavra = ValidarPalavra(Palavra, Jogador.Tentativas)
    if not Valido:
        await _AvisarJogadorSala(Sala, IdJogador, "chuteInvalido", MensagemOuPalavra)
        return {"valido": False, "mensagem": MensagemOuPalavra}

    PalavraNormalizada = MensagemOuPalavra
    if Gerenciador.AplicarChuteJogador(Sala, IdJogador, PalavraNormalizada):
        VerificarFimRodada(Sala)
    await BroadcastEstadoSala(Sala)
    Estado = Gerenciador.EstadoPublicoSala(Sala, IdJogador)
    return {"valido": True, "estado": Estado}


async def ConectarWebSocketSala(Conexao: WebSocket, codigo_sala: str, id_jogador: str) -> None:
    from nucleo.controle_carga import (
        LiberarConexaoWsSala,
        PodeAceitarWsSala,
        RegistrarConexaoWsSala,
    )
    from nucleo.redis_estado import VerificarWorkerDonoSala

    Codigo = codigo_sala.upper()
    DonoOk, WorkerRemoto = VerificarWorkerDonoSala(Codigo)
    if not DonoOk:
        await Conexao.close(
            code=1013,
            reason="Sala em outro processo — use um único termo-api.",
        )
        return
    Admissao = PodeAceitarWsSala()
    if not Admissao.Permitido:
        await Conexao.close(code=1013, reason=Admissao.Mensagem or "Servidor cheio")
        return
    await Conexao.accept()
    RegistrarConexaoWsSala()
    Sala = Gerenciador.ObterSala(codigo_sala)

    if not Sala or id_jogador not in Sala.Jogadores:
        LiberarConexaoWsSala()
        await Conexao.send_json({"tipo": "erro", "mensagem": "Sala ou jogador inválido."})
        await Conexao.close()
        return

    _, ExpulsosConexao = Gerenciador.LimparJogadoresInativos(Sala)
    for IdExpulso, Motivo in ExpulsosConexao:
        if IdExpulso == id_jogador:
            LiberarConexaoWsSala()
            if Motivo == "inatividade":
                Msg = (
                    "Você foi expulso da arena por inatividade "
                    "(2 minutos sem interação na sala de espera)."
                )
            else:
                Msg = "Você foi removido da sala por desconexão prolongada."
            await Conexao.send_json({"tipo": "expulso", "mensagem": Msg})
            await Conexao.close()
            return
    Gerenciador.MarcarConexao(Sala, id_jogador, True)
    RegistrarConexao(Sala.CodigoSala, id_jogador, Conexao)
    await Conexao.send_json(
        {
            "tipo": "conectado",
            "dados": Gerenciador.EstadoPublicoSala(Sala, id_jogador),
        }
    )
    Gerenciador.TentarInicioAutomatico(Sala)
    await BroadcastEstadoSala(Sala)

    SaidaExplicita = False
    try:
        while True:
            Texto = await Conexao.receive_text()
            try:
                Dados = json.loads(Texto)
            except json.JSONDecodeError:
                await EnviarParaJogador(
                    Sala.CodigoSala,
                    id_jogador,
                    {"tipo": "erro", "mensagem": "Mensagem inválida."},
                )
                continue
            Tipo = Dados.get("tipo")
            Payload = Dados.get("dados", {})
            SalaAtual = Gerenciador.ObterSala(Sala.CodigoSala)
            if not SalaAtual:
                break
            Sala = SalaAtual

            if Tipo in ("ativo", "ping"):
                Gerenciador.RegistrarAtividade(Sala, id_jogador)
                continue
            if Tipo != "sair":
                Gerenciador.RegistrarAtividade(Sala, id_jogador)

            if Tipo == "chute":
                await ProcessarChuteSala(Sala, id_jogador, Payload.get("palavra", ""))
            elif Tipo == "iniciar":
                Erro = Gerenciador.IniciarPartida(Sala, id_jogador)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "proximaRodada":
                Erro = Gerenciador.ProximaRodada(Sala, id_jogador)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "encerrarSessao":
                Erro = Gerenciador.EncerrarSessao(Sala, id_jogador)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    RegistrarRankingSessao(Sala)
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "pronto":
                Pronto = Payload.get("pronto")
                ProntoVal = None if Pronto is None else bool(Pronto)
                Erro = Gerenciador.AlternarPronto(Sala, id_jogador, ProntoVal)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "configurar":
                Erro = Gerenciador.AtualizarConfiguracaoSala(
                    Sala,
                    id_jogador,
                    bool(Payload.get("mesmaPalavra", True)),
                    bool(Payload.get("verOutros", True)),
                    int(Payload.get("maximoJogadores", 4)),
                    int(Payload.get("tempoLimiteSegundos", 0)),
                    str(Payload.get("modoSessao", "pontos")),
                    int(Payload.get("metaVitorias", 5)),
                    bool(Payload.get("inicioAutoDois", False)),
                    Payload.get("senhaNova"),
                    bool(Payload.get("removerSenha", False)),
                )
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "expulsar":
                IdAlvo = Payload.get("idJogador", "")
                Erro = Gerenciador.ExpulsarJogador(Sala, id_jogador, IdAlvo)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        IdAlvo,
                        {
                            "tipo": "expulso",
                            "mensagem": "Você foi removido da sala pelo host.",
                        },
                    )
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "chat":
                Erro = Gerenciador.AdicionarMensagemChat(
                    Sala, id_jogador, Payload.get("texto", "")
                )
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "revanche":
                Erro = Gerenciador.Revanche(Sala, id_jogador)
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "transferirHost":
                Erro = Gerenciador.TransferirHost(
                    Sala, id_jogador, Payload.get("idJogador", "")
                )
                if Erro:
                    await EnviarParaJogador(
                        Sala.CodigoSala,
                        id_jogador,
                        {"tipo": "erro", "mensagem": Erro},
                    )
                else:
                    await BroadcastEstadoSala(Sala)
            elif Tipo == "sair":
                SaidaExplicita = True
                break

    except WebSocketDisconnect:
        pass
    finally:
        LiberarConexaoWsSala()
        RemoverConexao(Sala.CodigoSala, id_jogador)
        if SaidaExplicita:
            from nucleo.partida_sessao import ProcessarSaidaJogadorOnline

            SalaSaida = Gerenciador.ObterSala(Sala.CodigoSala)
            if SalaSaida:
                ProcessarSaidaJogadorOnline(Gerenciador, SalaSaida, id_jogador)
        elif Gerenciador.ObterSala(Sala.CodigoSala):
            Gerenciador.MarcarConexao(Sala, id_jogador, False)
            Gerenciador.TransferirHostSePreciso(Sala)
        SalaAtual = Gerenciador.ObterSala(Sala.CodigoSala)
        if SalaAtual:
            Gerenciador.PersistirSala(SalaAtual)
            await BroadcastEstadoSala(SalaAtual)


def RegistrarWebSocket(Aplicacao) -> None:
    from nucleo.gerenciador_salas import RegistrarNotificadorLobbySalas

    RegistrarNotificadorLobbySalas(AgendarAtualizacaoLobbySalas)

    @Aplicacao.websocket("/ws/lobby")
    async def LobbyWebSocket(Conexao: WebSocket):
        await ConectarWebSocketLobby(Conexao)

    @Aplicacao.websocket("/ws/sala/{codigo_sala}/{id_jogador}")
    async def SalaWebSocket(Conexao: WebSocket, codigo_sala: str, id_jogador: str):
        await ConectarWebSocketSala(Conexao, codigo_sala, id_jogador)

    @Aplicacao.websocket("/ws/versus/{codigo_sala}/{id_jogador}")
    async def VersusWebSocketLegado(Conexao: WebSocket, codigo_sala: str, id_jogador: str):
        await ConectarWebSocketSala(Conexao, codigo_sala, id_jogador)
