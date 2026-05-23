import time

from . import persistencia
from .arena_rodadas import FormatarModoSessao, ModoPontos
from .gerenciador_salas import ConfiguracaoSala, JogadorSala, SalaJogo
from .sala_chat import MaximoMensagensChat


def ExportarSnapshot(Sala: SalaJogo) -> dict:
    Config = Sala.Configuracao
    return {
        "idPartida": getattr(Sala, "IdPartida", None),
        "codigoSala": Sala.CodigoSala,
        "criadorId": Sala.CriadorId,
        "estadoSala": Sala.EstadoSala,
        "estadoSalaAntesPausa": getattr(Sala, "EstadoSalaAntesPausa", None),
        "pausaAteEpoch": getattr(Sala, "PausaAteEpoch", None),
        "idJogadorPausado": getattr(Sala, "IdJogadorPausado", None),
        "timersCongelados": getattr(Sala, "TimersCongelados", None) or {},
        "partidaEncerrada": Sala.PartidaEncerrada,
        "vencedorId": Sala.VencedorId,
        "palavraSecreta": Sala.PalavraSecreta,
        "palavraComAcento": Sala.PalavraComAcento,
        "configuracao": {
            "mesmaPalavra": Config.MesmaPalavra,
            "verOutros": Config.VerOutros,
            "maximoJogadores": Config.MaximoJogadores,
            "senha": Config.Senha,
            "tempoLimiteSegundos": Config.TempoLimiteSegundos,
            "numeroRodadas": Config.NumeroRodadas,
            "modoSessao": Config.ModoSessao,
            "metaVitorias": Config.MetaVitorias,
            "inicioAutoDois": Config.InicioAutoDois,
            "salaPublica": Config.SalaPublica,
            "ranqueada": Config.Ranqueada,
            "ehDesafio": Config.EhDesafio,
            "modoSessaoTexto": FormatarModoSessao(
                Config.ModoSessao, Config.MetaVitorias, Config.Ranqueada
            ),
        },
        "resultadosRanqueada": Sala.ResultadosRanqueada,
        "rodadaAtual": Sala.RodadaAtual,
        "historicoRodadas": Sala.HistoricoRodadas,
        "mensagensChat": Sala.MensagensChat[-MaximoMensagensChat:],
        "countdownFimEpoch": Sala.CountdownFimEpoch,
        "ultimoVencedorRodadaId": Sala.UltimoVencedorRodadaId,
        "jogadores": [
            {
                "idJogador": J.IdJogador,
                "nomeJogador": J.NomeJogador,
                "palavraSecreta": J.PalavraSecreta,
                "palavraComAcento": J.PalavraComAcento,
                "tentativas": J.Tentativas,
                "venceu": J.Venceu,
                "finalizou": J.Finalizou,
                "pontos": J.Pontos,
                "pontosAcumulados": J.PontosAcumulados,
                "pontosUltimaRodada": J.PontosUltimaRodada,
                "vitoriasRodada": J.VitoriasRodada,
                "tempoFimEpoch": J.TempoFimEpoch,
                "conectado": J.Conectado,
                "ultimaAtividade": J.UltimaAtividade,
                "espectador": J.Espectador,
                "idConta": J.IdConta,
                "pronto": J.Pronto,
                "tokenSessao": getattr(J, "TokenSessao", None),
                "ausenteContinua": getattr(J, "AusenteContinua", False),
                "desconexaoInicioEpoch": getattr(J, "DesconexaoInicioEpoch", None),
            }
            for J in Sala.Jogadores.values()
        ],
    }


def ImportarSnapshot(Dados: dict) -> SalaJogo | None:
    try:
        ConfigDados = Dados["configuracao"]
        Config = ConfiguracaoSala(
            MesmaPalavra=ConfigDados["mesmaPalavra"],
            VerOutros=ConfigDados["verOutros"],
            MaximoJogadores=ConfigDados["maximoJogadores"],
            Senha=ConfigDados.get("senha"),
            TempoLimiteSegundos=ConfigDados.get("tempoLimiteSegundos", 0),
            NumeroRodadas=ConfigDados.get("numeroRodadas", 0),
            ModoSessao=ConfigDados.get("modoSessao", ModoPontos),
            MetaVitorias=ConfigDados.get("metaVitorias", 5),
            InicioAutoDois=ConfigDados.get("inicioAutoDois", False),
            SalaPublica=ConfigDados.get("salaPublica", True),
            Ranqueada=ConfigDados.get("ranqueada", False),
            EhDesafio=ConfigDados.get("ehDesafio", False),
        )
        Jogadores = {}
        for J in Dados.get("jogadores", []):
            Jogadores[J["idJogador"]] = JogadorSala(
                IdJogador=J["idJogador"],
                NomeJogador=J["nomeJogador"],
                PalavraSecreta=J.get("palavraSecreta"),
                PalavraComAcento=J.get("palavraComAcento"),
                Tentativas=J.get("tentativas", []),
                Venceu=J.get("venceu", False),
                Finalizou=J.get("finalizou", False),
                Pontos=J.get("pontos", 0),
                PontosAcumulados=J.get("pontosAcumulados", 0),
                PontosUltimaRodada=J.get("pontosUltimaRodada", 0),
                VitoriasRodada=J.get("vitoriasRodada", 0),
                TempoFimEpoch=J.get("tempoFimEpoch"),
                Conectado=False,
                UltimaAtividade=J.get("ultimaAtividade", time.time()),
                Espectador=J.get("espectador", False),
                IdConta=J.get("idConta"),
                Pronto=J.get("pronto", False),
                EhBot=J.get("ehBot", False),
                TokenSessao=J.get("tokenSessao"),
                AusenteContinua=J.get("ausenteContinua", False),
                DesconexaoInicioEpoch=J.get("desconexaoInicioEpoch"),
            )
        from . import partida_sessao

        IdPartida = Dados.get("idPartida") or partida_sessao.GerarIdPartida()
        Sala = SalaJogo(
            CodigoSala=Dados["codigoSala"],
            CriadorId=Dados["criadorId"],
            Configuracao=Config,
            IdPartida=IdPartida,
            EstadoSala=Dados.get("estadoSala", "aguardando"),
            EstadoSalaAntesPausa=Dados.get("estadoSalaAntesPausa"),
            PausaAteEpoch=Dados.get("pausaAteEpoch"),
            IdJogadorPausado=Dados.get("idJogadorPausado"),
            TimersCongelados=dict(Dados.get("timersCongelados") or {}),
            PalavraSecreta=Dados.get("palavraSecreta"),
            PalavraComAcento=Dados.get("palavraComAcento"),
            Jogadores=Jogadores,
            PartidaEncerrada=Dados.get("partidaEncerrada", False),
            VencedorId=Dados.get("vencedorId"),
            RodadaAtual=Dados.get("rodadaAtual", 0),
            HistoricoRodadas=Dados.get("historicoRodadas", []),
            MensagensChat=Dados.get("mensagensChat", []),
            CountdownFimEpoch=Dados.get("countdownFimEpoch"),
            UltimoVencedorRodadaId=Dados.get("ultimoVencedorRodadaId"),
            ResultadosRanqueada=Dados.get("resultadosRanqueada"),
        )
        for J in Sala.Jogadores.values():
            partida_sessao.GarantirTokenJogador(J)
        persistencia.RegistrarPartidaSala(Sala.IdPartida, Sala.CodigoSala)
        return Sala
    except (KeyError, TypeError):
        return None


def RestaurarSalasAtivas(Gerenciador) -> None:
    for Codigo in persistencia.ListarSalasAtivas():
        if Codigo in Gerenciador.Salas:
            continue
        Dados = persistencia.CarregarSalaSnapshot(Codigo)
        if Dados:
            Sala = ImportarSnapshot(Dados)
            if Sala:
                Gerenciador.Salas[Codigo] = Sala


def PersistirSala(Gerenciador, Sala: SalaJogo | None) -> None:
    from .gerenciador_salas import _DispararNotificacaoLobby

    if not Sala:
        return
    if Sala.PartidaEncerrada or not Sala.Jogadores:
        persistencia.RemoverSala(Sala.CodigoSala)
        _DispararNotificacaoLobby()
        return
    persistencia.SalvarSalaSnapshot(Sala.CodigoSala, ExportarSnapshot(Sala))
    _DispararNotificacaoLobby()
