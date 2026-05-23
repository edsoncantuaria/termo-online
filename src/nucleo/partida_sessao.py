"""Sessão de partida online (arena/ranqueada): tokens, pausa, retomada, desistência e eventos."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from . import persistencia
from .gerenciador_salas import GerenciadorSalas, JogadorSala, SalaJogo

PAUSA_RANQUEADA_SEG = 60
PAUSA_DESAFIO_SEG = 30
PAUSA_ARENA_SEG = 300
ABANDONO_TOTAL_SEG = 180


def GerarIdPartida() -> str:
    return str(uuid.uuid4())


def GerarTokenSessao() -> str:
    return secrets.token_urlsafe(16)


def JogadorSemPontuacaoNaSessao(Jogador: JogadorSala) -> bool:
    """Sem chutes e sem pontos/vitórias na sessão — saída não conta no histórico nem em XP."""
    return (
        len(Jogador.Tentativas) == 0
        and getattr(Jogador, "PontosAcumulados", 0) == 0
        and getattr(Jogador, "VitoriasRodada", 0) == 0
    )


def PartidaEmAndamento(Sala: SalaJogo) -> bool:
    if Sala.PartidaEncerrada:
        return False
    return Sala.EstadoSala in (
        "jogando",
        "countdown",
        "entre_rodadas",
        "pausada",
    )


def SegundosPausaSala(Sala: SalaJogo) -> int:
    if Sala.Configuracao.Ranqueada:
        return PAUSA_RANQUEADA_SEG
    if Sala.Configuracao.EhDesafio:
        return PAUSA_DESAFIO_SEG
    return PAUSA_ARENA_SEG


def RegistrarEventoPartida(
    IdPartida: str,
    Tipo: str,
    Payload: dict | None = None,
    CodigoSala: str | None = None,
) -> None:
    persistencia.RegistrarEventoPartida(
        IdPartida,
        Tipo,
        json.dumps(Payload or {}, ensure_ascii=False),
        CodigoSala,
    )


def ValidarTokenJogador(Jogador: JogadorSala | None, Token: str | None) -> bool:
    if not Jogador or not getattr(Jogador, "TokenSessao", None):
        return False
    if not Token or not str(Token).strip():
        return False
    return secrets.compare_digest(Jogador.TokenSessao, str(Token).strip())


def ValidarAcessoJogador(
    Sala: SalaJogo,
    IdJogador: str,
    Token: str | None,
    IdConta: str | None = None,
) -> tuple[bool, str | None]:
    Jogador = Sala.Jogadores.get(IdJogador)
    if not Jogador:
        return False, "Jogador não encontrado nesta partida."
    if IdConta and Jogador.IdConta and Jogador.IdConta == IdConta:
        return True, None
    if ValidarTokenJogador(Jogador, Token):
        return True, None
    return False, "Token de sessão inválido."


def ObterSalaPorIdPartida(Gerenciador: GerenciadorSalas, IdPartida: str) -> SalaJogo | None:
    for Sala in Gerenciador.Salas.values():
        if getattr(Sala, "IdPartida", None) == IdPartida:
            return Sala
    Codigo = persistencia.ObterCodigoSalaPorIdPartida(IdPartida)
    if Codigo:
        Sala = Gerenciador.ObterSala(Codigo)
        if Sala:
            return Sala
    Gerenciador.RestaurarSalasAtivas()
    for Sala in Gerenciador.Salas.values():
        if getattr(Sala, "IdPartida", None) == IdPartida:
            return Sala
    if Codigo:
        return Gerenciador.ObterSala(Codigo)
    return None


def GarantirIdPartidaSala(Sala: SalaJogo) -> None:
    if not getattr(Sala, "IdPartida", None):
        Sala.IdPartida = GerarIdPartida()
        persistencia.RegistrarPartidaSala(Sala.IdPartida, Sala.CodigoSala)


def GarantirTokenJogador(Jogador: JogadorSala) -> None:
    if not getattr(Jogador, "TokenSessao", None):
        Jogador.TokenSessao = GerarTokenSessao()


def CamposPausaPublicos(Sala: SalaJogo) -> dict:
    if Sala.EstadoSala != "pausada":
        return {
            "pausada": False,
            "pausaAteEpoch": None,
            "segundosPausaRestantes": None,
            "idJogadorPausado": None,
            "motivoPausa": None,
        }
    Restante = None
    if Sala.PausaAteEpoch:
        Restante = max(0, int(Sala.PausaAteEpoch - time.time()))
    Segundos = SegundosPausaSala(Sala)
    if Sala.Configuracao.Ranqueada:
        Motivo = "Oponente desconectou — aguardando retorno…"
    elif Sala.Configuracao.EhDesafio:
        Motivo = (
            f"Jogador desconectou — aguardando retorno ({Segundos}s). "
            "Depois a partida continua sem ele."
        )
    else:
        Motivo = "Jogador desconectou — aguardando retorno…"
    return {
        "pausada": True,
        "pausaAteEpoch": Sala.PausaAteEpoch,
        "segundosPausaRestantes": Restante,
        "idJogadorPausado": Sala.IdJogadorPausado,
        "motivoPausa": Motivo,
    }


def _RestaurarTimersCongelados(Sala: SalaJogo) -> None:
    Agora = time.time()
    for IdJ, Segundos in (Sala.TimersCongelados or {}).items():
        J = Sala.Jogadores.get(IdJ)
        if J and Segundos > 0 and not J.Finalizou:
            J.TempoFimEpoch = Agora + Segundos
    Sala.TimersCongelados = {}


def IniciarPausaPorDesconexao(
    Gerenciador: GerenciadorSalas,
    Sala: SalaJogo,
    IdJogador: str,
) -> bool:
    if not PartidaEmAndamento(Sala):
        return False
    if Sala.EstadoSala == "pausada":
        return False
    Jogador = Sala.Jogadores.get(IdJogador)
    if not Jogador or Jogador.Espectador:
        return False
    Ativos = Gerenciador.JogadoresAtivos(Sala)
    if len(Ativos) < 2 and not Sala.Configuracao.Ranqueada:
        return False

    if not Jogador.DesconexaoInicioEpoch:
        Jogador.DesconexaoInicioEpoch = time.time()

    GarantirIdPartidaSala(Sala)
    Sala.EstadoSalaAntesPausa = Sala.EstadoSala if Sala.EstadoSala != "pausada" else (
        Sala.EstadoSalaAntesPausa or "jogando"
    )
    Sala.EstadoSala = "pausada"
    Sala.IdJogadorPausado = IdJogador
    Sala.PausaAteEpoch = time.time() + SegundosPausaSala(Sala)
    Sala.TimersCongelados = {}

    Agora = time.time()
    for J in Ativos:
        if J.IdJogador == IdJogador:
            continue
        if J.TempoFimEpoch and not J.Finalizou:
            Sala.TimersCongelados[J.IdJogador] = max(0.0, J.TempoFimEpoch - Agora)
            J.TempoFimEpoch = None

    RegistrarEventoPartida(
        Sala.IdPartida,
        "disconnect",
        {"idJogador": IdJogador, "segundosPausa": SegundosPausaSala(Sala)},
        Sala.CodigoSala,
    )
    Gerenciador.PersistirSala(Sala)
    return True


def RetomarPausaPorConexao(
    Gerenciador: GerenciadorSalas,
    Sala: SalaJogo,
    IdJogador: str,
) -> bool:
    if Sala.EstadoSala != "pausada" or Sala.IdJogadorPausado != IdJogador:
        return False

    Sala.EstadoSala = Sala.EstadoSalaAntesPausa or "jogando"
    Sala.EstadoSalaAntesPausa = None
    Sala.PausaAteEpoch = None
    Sala.IdJogadorPausado = None
    _RestaurarTimersCongelados(Sala)

    RegistrarEventoPartida(
        Sala.IdPartida,
        "retomada",
        {"idJogador": IdJogador},
        Sala.CodigoSala,
    )
    Gerenciador.PersistirSala(Sala)
    return True


def LimparEstadoPausa(Sala: SalaJogo) -> None:
    Sala.EstadoSalaAntesPausa = None
    Sala.PausaAteEpoch = None
    Sala.IdJogadorPausado = None
    Sala.TimersCongelados = {}


def EncerrarPausaSuave(Gerenciador: GerenciadorSalas, Sala: SalaJogo) -> bool:
    if Sala.EstadoSala != "pausada" or not Sala.IdJogadorPausado:
        return False

    IdAusente = Sala.IdJogadorPausado
    Jogador = Sala.Jogadores.get(IdAusente)
    GarantirIdPartidaSala(Sala)
    if Jogador:
        if not Jogador.DesconexaoInicioEpoch:
            Jogador.DesconexaoInicioEpoch = time.time()
        Jogador.AusenteContinua = True

    EstadoRetorno = Sala.EstadoSalaAntesPausa or "jogando"
    Sala.EstadoSala = EstadoRetorno
    LimparEstadoPausa(Sala)
    _RestaurarTimersCongelados(Sala)

    RegistrarEventoPartida(
        Sala.IdPartida,
        "pausa_expirada_continua",
        {"idJogador": IdAusente},
        Sala.CodigoSala,
    )

    if Sala.EstadoSala == "jogando":
        Gerenciador.FinalizarAusentesRodadaAtual(Sala)
    Gerenciador.PersistirSala(Sala)
    return True


def AplicarAbandonoDefinitivo(
    Gerenciador: GerenciadorSalas,
    Sala: SalaJogo,
    IdJogador: str,
) -> bool:
    Jogador = Sala.Jogadores.get(IdJogador)
    if not Jogador or not Jogador.AusenteContinua:
        return False

    GarantirIdPartidaSala(Sala)
    RegistrarEventoPartida(
        Sala.IdPartida,
        "abandono_tempo_maximo",
        {"idJogador": IdJogador},
        Sala.CodigoSala,
    )

    if Sala.EstadoSala == "pausada" and Sala.IdJogadorPausado == IdJogador:
        Retorno = Sala.EstadoSalaAntesPausa or "jogando"
        LimparEstadoPausa(Sala)
        Sala.EstadoSala = Retorno

    Ativos = [
        J
        for J in Gerenciador.JogadoresAtivos(Sala)
        if J.IdJogador != IdJogador
    ]

    if Sala.Configuracao.Ranqueada and Ativos:
        Gerenciador.EncerrarSessao(Sala, VencedorForcado=Ativos[0].IdJogador)
        return True

    Gerenciador.RemoverJogador(Sala.CodigoSala, IdJogador, Persistir=True)
    SalaRestante = Gerenciador.ObterSala(Sala.CodigoSala)
    if (
        SalaRestante
        and SalaRestante.EstadoSala == "pausada"
        and SalaRestante.IdJogadorPausado == IdJogador
    ):
        SalaRestante.EstadoSala = SalaRestante.EstadoSalaAntesPausa or "jogando"
        LimparEstadoPausa(SalaRestante)
        Gerenciador.PersistirSala(SalaRestante)
    return True


def VerificarPausasExpiradas(Gerenciador: GerenciadorSalas) -> list[SalaJogo]:
    Agora = time.time()
    Alteradas: list[SalaJogo] = []
    for Sala in list(Gerenciador.Salas.values()):
        if (
            Sala.EstadoSala == "pausada"
            and Sala.PausaAteEpoch
            and Agora >= Sala.PausaAteEpoch
        ):
            if EncerrarPausaSuave(Gerenciador, Sala):
                Alteradas.append(Gerenciador.ObterSala(Sala.CodigoSala) or Sala)
    return Alteradas


def VerificarAbandonosProlongados(Gerenciador: GerenciadorSalas) -> list[SalaJogo]:
    Agora = time.time()
    Alteradas: list[SalaJogo] = []
    for Sala in list(Gerenciador.Salas.values()):
        if Sala.PartidaEncerrada:
            continue
        for Jogador in Gerenciador.JogadoresAtivos(Sala):
            if not Jogador.AusenteContinua or not Jogador.DesconexaoInicioEpoch:
                continue
            if Agora - Jogador.DesconexaoInicioEpoch < ABANDONO_TOTAL_SEG:
                continue
            if AplicarAbandonoDefinitivo(Gerenciador, Sala, Jogador.IdJogador):
                Alteradas.append(Gerenciador.ObterSala(Sala.CodigoSala) or Sala)
                break
    return Alteradas


def MontarRetomarPartida(
    Gerenciador: GerenciadorSalas,
    Sala: SalaJogo,
    IdJogador: str,
) -> dict:
    Jogador = Sala.Jogadores[IdJogador]
    GarantirTokenJogador(Jogador)
    Estado = Gerenciador.EstadoPublicoSala(Sala, IdJogador)
    Estado["idJogador"] = IdJogador
    Estado["nomeJogador"] = Jogador.NomeJogador
    Estado["idPartida"] = Sala.IdPartida
    Estado["tokenSessao"] = Jogador.TokenSessao
    Estado["podeRetomar"] = PartidaEmAndamento(Sala)
    return Estado


def RetomarPartida(
    Gerenciador: GerenciadorSalas,
    IdPartida: str,
    Token: str | None,
    IdJogador: str | None = None,
    IdConta: str | None = None,
) -> tuple[dict | None, str | None, int]:
    Gerenciador.RestaurarSalasAtivas()
    Sala = ObterSalaPorIdPartida(Gerenciador, IdPartida)
    if not Sala:
        return None, "Partida não encontrada.", 404
    if Sala.PartidaEncerrada:
        return None, "Partida já encerrada.", 410

    Jogador = None
    if IdJogador and IdJogador in Sala.Jogadores:
        Ok, Erro = ValidarAcessoJogador(Sala, IdJogador, Token, IdConta)
        if not Ok:
            return None, Erro or "Acesso negado.", 403
        Jogador = Sala.Jogadores[IdJogador]
    elif IdConta:
        for J in Sala.Jogadores.values():
            if J.IdConta == IdConta:
                Jogador = J
                IdJogador = J.IdJogador
                break
        if not Jogador:
            return None, "Conta não participa desta partida.", 403
    else:
        return None, "Informe idJogador e token ou faça login na conta.", 400

    GarantirIdPartidaSala(Sala)
    GarantirTokenJogador(Jogador)
    RegistrarEventoPartida(
        Sala.IdPartida,
        "retomar_api",
        {"idJogador": IdJogador},
        Sala.CodigoSala,
    )
    Gerenciador.PersistirSala(Sala)
    return MontarRetomarPartida(Gerenciador, Sala, IdJogador), None, 200


def DesistirPartida(
    Gerenciador: GerenciadorSalas,
    IdPartida: str,
    IdJogador: str,
    Token: str | None,
) -> tuple[dict | None, str | None, int]:
    Gerenciador.RestaurarSalasAtivas()
    Sala = ObterSalaPorIdPartida(Gerenciador, IdPartida)
    if not Sala:
        return None, "Partida não encontrada.", 404

    Ok, Erro = ValidarAcessoJogador(Sala, IdJogador, Token)
    if not Ok:
        return None, Erro or "Acesso negado.", 403

    GarantirIdPartidaSala(Sala)
    RegistrarEventoPartida(
        Sala.IdPartida,
        "desistencia",
        {"idJogador": IdJogador},
        Sala.CodigoSala,
    )

    if Sala.EstadoSala == "pausada" and Sala.IdJogadorPausado == IdJogador:
        Retorno = Sala.EstadoSalaAntesPausa or "jogando"
        LimparEstadoPausa(Sala)
        Sala.EstadoSala = Retorno

    Jogador = Sala.Jogadores.get(IdJogador)
    if Jogador:
        Jogador.AusenteContinua = False
        Jogador.DesconexaoInicioEpoch = None

    Ativos = Gerenciador.JogadoresAtivos(Sala)
    Oponentes = [J for J in Ativos if J.IdJogador != IdJogador]

    SemPenalidade = bool(Jogador and JogadorSemPontuacaoNaSessao(Jogador))

    if Sala.Configuracao.Ranqueada and Oponentes:
        if SemPenalidade:
            Gerenciador.EncerrarSessaoCancelada(Sala)
            SalaFinal = Gerenciador.ObterSala(Sala.CodigoSala) or Sala
            return {
                "desistiu": True,
                "semPenalidade": True,
                "partidaCancelada": True,
                "partidaEncerrada": True,
                "codigoSala": Sala.CodigoSala,
                "estado": Gerenciador.EstadoPublicoSala(SalaFinal, IdJogador),
            }, None, 200
        Gerenciador.EncerrarSessao(Sala, VencedorForcado=Oponentes[0].IdJogador)
        SalaFinal = Gerenciador.ObterSala(Sala.CodigoSala) or Sala
        return {
            "desistiu": True,
            "semPenalidade": False,
            "partidaEncerrada": True,
            "codigoSala": Sala.CodigoSala,
            "estado": Gerenciador.EstadoPublicoSala(SalaFinal, IdJogador),
        }, None, 200

    Gerenciador.RemoverJogador(Sala.CodigoSala, IdJogador)
    SalaRestante = Gerenciador.ObterSala(Sala.CodigoSala)
    return {
        "desistiu": True,
        "semPenalidade": SemPenalidade,
        "partidaEncerrada": not SalaRestante or SalaRestante.PartidaEncerrada,
        "codigoSala": Sala.CodigoSala,
    }, None, 200
