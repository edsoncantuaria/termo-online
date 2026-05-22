from fastapi import APIRouter, Depends, HTTPException

from nucleo import persistencia
from nucleo.dicionario import ObterPalavraComAcento
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
    MaximoTentativasModo,
    ModoDesafio,
)
from nucleo.palavra_diaria import EscolherPalavraDoDia
from nucleo.pontuacao import CalcularPontuacao, RegistrarPontuacao
from servidor.dependencias_auth import ContaOpcional, ContaRegistrada
from servidor.partida_solo import (
    MontarRespostaPartida,
    NovaPartida,
    ObterPartida,
    SalvarPartida,
)
from servidor.rotas.schemas import (
    ChuteSoloRequest,
    GradeDiariaRequest,
    IniciarJogoRequest,
    IniciarSoloRequest,
)


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

    Partida = NovaPartida(
        PalavraSecreta=Tabuleiros[0]["palavraSecreta"],
        PalavraComAcento=Tabuleiros[0]["palavraComAcento"],
        Modo=Corpo.modo,
        Tabuleiros=Tabuleiros,
        DataDia=DataDia,
        Dificuldade=Corpo.dificuldade,
        CodigoDesafio=CodigoDesafio,
        NomeJogador=Nome,
        IdConta=IdConta,
    )
    if Corpo.modo == ModoDiaria and IdConta and DataDia:
        persistencia.IniciarSessaoDiariaConta(IdConta, DataDia, Partida.IdPartida)
    Resposta = MontarRespostaPartida(Partida)
    Resposta["nomeJogador"] = Nome
    return Resposta


def RegistrarRotasJogo(Roteador: APIRouter) -> None:
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

        Valido, MensagemOuPalavra = ValidarPalavra(
            Corpo.palavra,
            Partida.Tentativas,
            ModoDificil=Partida.Dificuldade == DificuldadeDificil,
        )
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
                IdConta=IdConta if Perfil and not Perfil.get("ehVisitante") else None,
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
                Resposta["palavrasSecretas"] = [
                    T["palavraComAcento"] for T in Partida.Tabuleiros
                ]
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

    @Roteador.post("/diaria/grade")
    def SalvarGradeDiaria(Corpo: GradeDiariaRequest, Perfil=Depends(ContaRegistrada)):
        _, _, DataDia = EscolherPalavraDoDia()
        IdConta = Perfil["idConta"]
        if not persistencia.JaJogouDiariaConta(IdConta, DataDia):
            raise HTTPException(
                status_code=400,
                detail="Conclua a palavra do dia antes de salvar a grade.",
            )
        NickNorm = Corpo.nick.strip()[:24].lower() or "jogador"
        NickConta = (Perfil.get("nick") or "").strip()[:24].lower()
        if NickNorm != NickConta:
            raise HTTPException(status_code=403, detail="Nick não corresponde à conta.")
        if not Corpo.gradeTexto or not Corpo.gradeTexto.strip():
            raise HTTPException(status_code=400, detail="Grade vazia.")
        if not persistencia.AtualizarGradeDiariaConta(
            IdConta, DataDia, Corpo.gradeTexto.strip()
        ):
            raise HTTPException(status_code=400, detail="Registro da diária não encontrado.")
        return {"salvo": True}

    @Roteador.get("/diaria/historico")
    def HistoricoDiaria(nick: str = "Jogador"):
        NickNorm = nick.strip()[:24].lower() or "jogador"
        return {"historico": persistencia.ListarHistoricoDiaria(NickNorm, 30)}
