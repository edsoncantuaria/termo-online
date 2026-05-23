"""Sessão de jogo ativa por conta (arena/ranqueada/solo) — persistência no banco."""

from __future__ import annotations

from . import persistencia
from .gerenciador_salas import GerenciadorSalas, SalaJogo


def SincronizarSessoesContaDaSala(Gerenciador: GerenciadorSalas, Sala: SalaJogo) -> None:
    from . import partida_sessao

    if Sala.PartidaEncerrada or not Sala.Jogadores:
        for J in Sala.Jogadores.values():
            if J.IdConta:
                persistencia.LimparSessaoJogoConta(J.IdConta)
        return

    EmAndamento = partida_sessao.PartidaEmAndamento(Sala)
    Pausa = partida_sessao.CamposPausaPublicos(Sala)
    Tipo = "ranqueada" if Sala.Configuracao.Ranqueada else "arena"
    TempoLimite = Sala.Configuracao.TempoLimiteSegundos or 0

    for J in Gerenciador.JogadoresAtivos(Sala):
        if not J.IdConta or J.Espectador:
            continue
        if not EmAndamento:
            persistencia.LimparSessaoJogoConta(J.IdConta)
            continue
        partida_sessao.GarantirIdPartidaSala(Sala)
        partida_sessao.GarantirTokenJogador(J)
        persistencia.SalvarSessaoJogoConta(
            IdConta=J.IdConta,
            Tipo=Tipo,
            IdPartida=Sala.IdPartida,
            CodigoSala=Sala.CodigoSala,
            IdJogador=J.IdJogador,
            TokenSessao=J.TokenSessao,
            EstadoSala=Sala.EstadoSala,
            Pausada=bool(Pausa.get("pausada")),
            SegundosPausa=Pausa.get("segundosPausaRestantes"),
            TempoLimiteSegundos=TempoLimite,
        )


def SincronizarSoloConta(Partida) -> None:
    IdConta = getattr(Partida, "IdConta", None)
    if not IdConta:
        return
    if getattr(Partida, "Encerrada", False):
        persistencia.LimparSessaoJogoConta(IdConta)
        return
    persistencia.SalvarSessaoJogoConta(
        IdConta=IdConta,
        Tipo="solo",
        IdPartida=Partida.IdPartida,
        IdJogador=IdConta,
        TokenPartida=getattr(Partida, "TokenPartida", None),
        ModoSolo=Partida.Modo,
        EstadoSala="jogando",
        Pausada=False,
    )


def LimparSessaoContaJogador(IdConta: str | None) -> None:
    if IdConta:
        persistencia.LimparSessaoJogoConta(IdConta)


def _TituloTipo(Tipo: str, ModoSolo: str | None = None) -> str:
    if Tipo == "ranqueada":
        return "Duelo ranqueado"
    if Tipo == "arena":
        return "Arena online"
    Rotulos = {
        "diaria": "Palavra do dia",
        "pratica": "Prática",
        "dueto": "Dueto",
        "quarteto": "Quarteto",
        "desafio": "Desafio",
    }
    return Rotulos.get(ModoSolo or "", "Partida solo")


def _TextoEstado(
    Tipo: str,
    EstadoSala: str | None,
    Pausada: bool,
    SegundosPausa: int | None,
    TempoLimiteSegundos: int,
) -> str:
    if Pausada:
        if SegundosPausa is not None:
            return f"Partida pausada — aguardando retorno (até {SegundosPausa}s)"
        return "Partida pausada — aguardando reconexão"
    if EstadoSala == "jogando":
        if Tipo == "ranqueada" and TempoLimiteSegundos > 0:
            return f"Rodada em andamento — limite de {TempoLimiteSegundos // 60} min por jogador"
        if TempoLimiteSegundos > 0:
            return f"Rodada em andamento — tempo limite {TempoLimiteSegundos // 60} min"
        return "Rodada em andamento"
    if EstadoSala == "entre_rodadas":
        return "Entre rodadas"
    if EstadoSala == "countdown":
        return "Próxima rodada em instantes"
    if EstadoSala == "aguardando":
        return "Sala aberta — aguardando início"
    return "Partida em andamento"


def MontarJogoAtivoParaConta(
    Gerenciador: GerenciadorSalas,
    IdConta: str,
) -> dict | None:
    from . import partida_sessao

    Linha = persistencia.ObterSessaoJogoConta(IdConta)
    if not Linha:
        return None

    Tipo = Linha["tipo"]
    if Tipo in ("arena", "ranqueada"):
        Gerenciador.RestaurarSalasAtivas()
        Codigo = (Linha.get("codigo_sala") or "").upper()
        Sala = Gerenciador.ObterSala(Codigo) if Codigo else None
        IdJogador = Linha.get("id_jogador")
        if (
            not Sala
            or not IdJogador
            or IdJogador not in Sala.Jogadores
            or Sala.PartidaEncerrada
        ):
            persistencia.LimparSessaoJogoConta(IdConta)
            return None
        J = Sala.Jogadores[IdJogador]
        if J.Espectador or not partida_sessao.PartidaEmAndamento(Sala):
            persistencia.LimparSessaoJogoConta(IdConta)
            return None
        Pausa = partida_sessao.CamposPausaPublicos(Sala)
        SincronizarSessoesContaDaSala(Gerenciador, Sala)
        Pausada = bool(Pausa.get("pausada"))
        SegundosPausa = Pausa.get("segundosPausaRestantes")
        TempoLimite = Sala.Configuracao.TempoLimiteSegundos or 0
        return {
            "ativo": True,
            "tipo": Tipo,
            "titulo": _TituloTipo(Tipo),
            "codigoSala": Sala.CodigoSala,
            "idPartida": Sala.IdPartida,
            "idJogador": IdJogador,
            "tokenSessao": J.TokenSessao or Linha.get("token_sessao"),
            "estadoSala": Sala.EstadoSala,
            "pausada": Pausada,
            "segundosPausaRestantes": SegundosPausa,
            "tempoLimiteSegundos": TempoLimite,
            "emTempoDeJogo": Sala.EstadoSala == "jogando" and not Pausada,
            "textoEstado": _TextoEstado(
                Tipo, Sala.EstadoSala, Pausada, SegundosPausa, TempoLimite
            ),
            "souCriador": Sala.CriadorId == IdJogador,
        }

    if Tipo == "solo":
        from servidor.partida_solo import ObterPartida

        Partida = ObterPartida(Linha["id_partida"])
        if not Partida or Partida.Encerrada:
            persistencia.LimparSessaoJogoConta(IdConta)
            return None
        if Partida.IdConta and Partida.IdConta != IdConta:
            persistencia.LimparSessaoJogoConta(IdConta)
            return None
        Modo = Partida.Modo
        return {
            "ativo": True,
            "tipo": "solo",
            "titulo": _TituloTipo("solo", Modo),
            "modoSolo": Modo,
            "idPartida": Partida.IdPartida,
            "idJogador": IdConta,
            "tokenPartida": Partida.TokenPartida or Linha.get("token_partida"),
            "estadoSala": "jogando",
            "pausada": False,
            "segundosPausaRestantes": None,
            "tempoLimiteSegundos": 0,
            "emTempoDeJogo": True,
            "textoEstado": "Partida solo em andamento",
        }

    persistencia.LimparSessaoJogoConta(IdConta)
    return None
