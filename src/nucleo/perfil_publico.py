"""Perfil público de outro jogador (busca por nick)."""

from __future__ import annotations

from .contas import MontarPerfilConta, ValidarNick
from . import persistencia
from .bots_ranqueados import (
    BotsRanqueadosAtivos,
    EstatisticasBot,
    ObterBotPorNick,
    PontosBotAtual,
)
from .estatisticas import MontarListaPartidasPorModo, ObterEstatisticasJogador
from .ranqueada import MontarCamposRankExibicao
from .ranking_ranqueado import MontarRankingCompleto


def MontarPerfilPublico(Conta: dict) -> dict:
    P = MontarPerfilConta(Conta)
    Publico = {
        "nick": P["nick"],
        "avatarId": P["avatarId"],
        "ehVisitante": P["ehVisitante"],
        "pontosRanqueada": P["pontosRanqueada"],
        "elo": P["elo"],
        "eloNome": P["eloNome"],
        "eloClasse": P["eloClasse"],
        "rotuloRank": P["rotuloRank"],
        "semRank": P["semRank"],
        "partidasRanqueadas": P["partidasRanqueadas"],
        "vitoriasRanqueadas": P["vitoriasRanqueadas"],
        "partidasTreinoRanqueado": P["partidasTreinoRanqueado"],
        "vitoriasTreinoRanqueado": P["vitoriasTreinoRanqueado"],
        "partidasTemporada": P["partidasTemporada"],
        "vitoriasTemporada": P["vitoriasTemporada"],
        "podeRanqueada": P["podeRanqueada"],
    }
    Prog = P.get("progresso")
    if Prog:
        Publico["nivel"] = Prog["nivel"]
        Publico["faixaNome"] = Prog["estiloNivel"]["faixaNome"]
        Publico["xpTotal"] = Prog["xpTotal"]
    return Publico


def MontarEstatisticasBot(Nick: str, Partidas: int, Vitorias: int) -> dict:
    Distribuicao = {str(I): 0 for I in range(1, 7)}
    PartidasPorModo = MontarListaPartidasPorModo({}, Partidas, Vitorias)
    return {
        "nick": Nick,
        "partidasRanking": Partidas,
        "vitoriasRanking": Vitorias,
        "taxaVitoria": round(100 * Vitorias / Partidas, 1) if Partidas else 0,
        "distribuicaoTentativas": Distribuicao,
        "diariasRecentes": 0,
        "diariasVencidas": 0,
        "historicoDiaria": [],
        "partidasPorModo": PartidasPorModo,
        "totalPartidasSolo": 0,
    }


def MontarPerfilBot(Bot) -> dict:
    Partidas, Vitorias = EstatisticasBot(Bot.Id)
    Pontos = PontosBotAtual(Bot.Id)
    Campos = MontarCamposRankExibicao(Partidas, Pontos)
    return {
        "nick": Bot.Nick,
        "avatarId": None,
        "ehVisitante": False,
        "pontosRanqueada": Pontos,
        "partidasRanqueadas": Partidas,
        "vitoriasRanqueadas": Vitorias,
        "partidasTreinoRanqueado": 0,
        "vitoriasTreinoRanqueado": 0,
        "partidasTemporada": 0,
        "vitoriasTemporada": 0,
        "podeRanqueada": True,
        **Campos,
    }


def _RespostaPerfilVisitante(NickNorm: str, Conta: dict | None) -> dict:
    """Conta visitante ou nick inexistente — sem estatísticas públicas."""
    if Conta and Conta.get("eh_visitante"):
        Mensagem = (
            "Este nick é de uma conta visitante (sem e-mail). "
            "Visitantes não têm perfil público nem posição no ranking."
        )
        PerfilMin = {
            "nick": Conta["nick"],
            "avatarId": Conta.get("avatar_id"),
            "ehVisitante": True,
        }
        Encontrado = True
    else:
        Mensagem = (
            "Nenhuma conta registrada com este nick. "
            "A busca mostra jogadores com conta (e-mail) ou perfis do ranqueado."
        )
        PerfilMin = {"nick": NickNorm, "ehVisitante": True}
        Encontrado = False
    return {
        "tipo": "visitante",
        "nick": PerfilMin["nick"],
        "mensagem": Mensagem,
        "perfil": PerfilMin,
        "estatisticas": None,
        "ultimasPartidas": [],
        "limitePartidas": persistencia.LIMITE_ULTIMAS_PARTIDAS,
        "posicaoRanqueada": None,
        "totalRanqueados": None,
        "encontrado": Encontrado,
    }


def BuscarPerfilBot(NickNorm: str, Bot) -> dict:
    Perfil = MontarPerfilBot(Bot)
    Partidas, Vitorias = EstatisticasBot(Bot.Id)
    Stats = MontarEstatisticasBot(Bot.Nick, Partidas, Vitorias)
    Ultimas = persistencia.ListarUltimasPartidasBot(
        Bot.Id, persistencia.LIMITE_ULTIMAS_PARTIDAS
    )
    Ranking = MontarRankingCompleto({"nick": Bot.Nick.lower()})
    return {
        "tipo": "registrado",
        "nick": Bot.Nick,
        "mensagem": None,
        "perfil": Perfil,
        "estatisticas": Stats,
        "ultimasPartidas": Ultimas,
        "limitePartidas": persistencia.LIMITE_ULTIMAS_PARTIDAS,
        "posicaoRanqueada": Ranking.get("minhaPosicao"),
        "totalRanqueados": Ranking.get("totalRanqueados", 0),
    }


def BuscarPerfilJogador(Nick: str) -> dict:
    """
    tipo: registrado | visitante
    - registrado: conta com e-mail (perfil completo público)
    - visitante: sem conta registrada ou conta visitante (dados limitados)
    """
    try:
        NickNorm = ValidarNick(Nick)
    except ValueError as Erro:
        raise ValueError(str(Erro)) from Erro

    Conta = persistencia.ObterContaPorNick(NickNorm)
    Registrado = bool(Conta and not Conta.get("eh_visitante"))

    if not Registrado and BotsRanqueadosAtivos():
        Bot = ObterBotPorNick(NickNorm)
        if Bot:
            return BuscarPerfilBot(NickNorm, Bot)

    if Conta and Conta.get("eh_visitante"):
        return _RespostaPerfilVisitante(NickNorm, Conta)

    if Registrado:
        PerfilConta = MontarPerfilConta(Conta)
        Perfil = MontarPerfilPublico(Conta)
        Stats = ObterEstatisticasJogador(
            NickNorm, IdConta=Conta["id"], Perfil=PerfilConta
        )
        Partidas = persistencia.ListarUltimasPartidasConta(
            Conta["id"], persistencia.LIMITE_ULTIMAS_PARTIDAS
        )
        Ranking = MontarRankingCompleto(
            {
                "nick": PerfilConta["nick"].lower(),
                "ehVisitante": False,
                "pontosRanqueada": PerfilConta["pontosRanqueada"],
                "elo": PerfilConta["elo"],
                "eloNome": PerfilConta["eloNome"],
                "partidasRanqueadas": PerfilConta["partidasRanqueadas"],
                "vitoriasRanqueadas": PerfilConta["vitoriasRanqueadas"],
            }
        )
        return {
            "tipo": "registrado",
            "nick": Perfil["nick"],
            "mensagem": None,
            "perfil": Perfil,
            "estatisticas": Stats,
            "ultimasPartidas": Partidas,
            "limitePartidas": persistencia.LIMITE_ULTIMAS_PARTIDAS,
            "posicaoRanqueada": Ranking.get("minhaPosicao"),
            "totalRanqueados": Ranking.get("totalRanqueados", 0),
        }

    return _RespostaPerfilVisitante(NickNorm, None)
