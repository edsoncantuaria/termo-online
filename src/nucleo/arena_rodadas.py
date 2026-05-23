"""Pontuação e fluxo de rodadas da Arena."""

from .logica_jogo import MaximoTentativas

ModoPontos = "pontos"
ModoVitorias = "vitorias"


def FormatarModoSessao(
    Modo: str, MetaVitorias: int = 5, Ranqueada: bool = False
) -> str:
    if Ranqueada:
        return "Ranqueado 1v1"
    if Modo == ModoVitorias:
        return f"Primeiro a {MetaVitorias} vitórias"
    return "Pontos infinitos (maratona)"


def SessaoAtingiuLimite(
    Modo: str,
    RodadaAtual: int,
    NumeroRodadas: int,
    Jogadores: dict,
    MetaVitorias: int,
) -> bool:
    if Modo == ModoVitorias:
        return any(
            getattr(J, "VitoriasRodada", 0) >= MetaVitorias for J in Jogadores.values()
        )
    return NumeroRodadas > 0 and RodadaAtual >= NumeroRodadas


def CalcularPontosRodada(Venceu: bool, TentativasUsadas: int) -> int:
    if not Venceu or TentativasUsadas < 1:
        return 0
    return max(1, 7 - min(TentativasUsadas, MaximoTentativas))


def ContarVerdesTentativa(Tentativa: dict) -> int:
    Estados = Tentativa.get("estados") or []
    return sum(1 for E in Estados if E == "correto")


def MelhorContagemVerdes(Jogador) -> int:
    if not Jogador.Tentativas:
        return 0
    return max(ContarVerdesTentativa(T) for T in Jogador.Tentativas)


def DeterminarVencedoresRodadaPorVerdes(Jogadores: list) -> tuple[list[str], int]:
    """Quem teve mais letras verdes na melhor tentativa; empate divide o ponto."""
    if not Jogadores:
        return [], 0
    Pontuacao = [(J.IdJogador, MelhorContagemVerdes(J)) for J in Jogadores]
    MaxVerdes = max(P for _, P in Pontuacao)
    if MaxVerdes < 1:
        return [], 0
    Vencedores = [Id for Id, P in Pontuacao if P == MaxVerdes]
    return Vencedores, MaxVerdes


def DeterminarVencedorRodada(Sala) -> str | None:
    """Um vencedor por rodada (para modo primeiro a N vitórias)."""
    Jogadores = [
        J for J in Sala.Jogadores.values() if not getattr(J, "Espectador", False)
    ]
    if not Jogadores:
        return None

    Config = Sala.Configuracao
    Vencedores = [J for J in Jogadores if J.Venceu]
    if Config.MesmaPalavra:
        if not Vencedores:
            return None
        return min(Vencedores, key=lambda J: len(J.Tentativas)).IdJogador

    def Chave(J):
        Tent = len(J.Tentativas) or MaximoTentativas
        Pts = CalcularPontosRodada(J.Venceu, Tent)
        return (Pts, 1 if J.Venceu else 0, -Tent)

    Melhor = max(Jogadores, key=Chave)
    if Melhor.Venceu or CalcularPontosRodada(Melhor.Venceu, len(Melhor.Tentativas) or MaximoTentativas) > 0:
        return Melhor.IdJogador
    VencedoresVerdes, _ = DeterminarVencedoresRodadaPorVerdes(Jogadores)
    if len(VencedoresVerdes) == 1:
        return VencedoresVerdes[0]
    return None


def JogadorAtingiuMetaVitorias(Jogadores: dict, Meta: int) -> str | None:
    for J in Jogadores.values():
        if getattr(J, "VitoriasRodada", 0) >= Meta:
            return J.IdJogador
    return None


def MontarPlacar(Jogadores: dict, Modo: str = ModoPontos, MetaVitorias: int = 5) -> list[dict]:
    Itens = [
        {
            "idJogador": J.IdJogador,
            "nomeJogador": J.NomeJogador,
            "pontosAcumulados": getattr(J, "PontosAcumulados", 0),
            "pontosUltimaRodada": getattr(J, "PontosUltimaRodada", 0),
            "vitoriasRodada": getattr(J, "VitoriasRodada", 0),
        }
        for J in Jogadores.values()
    ]
    if Modo == ModoVitorias:
        return sorted(
            Itens,
            key=lambda I: (-I["vitoriasRodada"], -I["pontosAcumulados"], I["nomeJogador"]),
        )
    return sorted(
        Itens,
        key=lambda I: (-I["pontosAcumulados"], -I["vitoriasRodada"], I["nomeJogador"]),
    )


def MontarMensagemFimRodada(
    HistoricoRodadas: list,
    IdObservador: str,
    Jogadores: dict,
) -> str | None:
    """Texto para o jogador ao fim da rodada (acerto, mais perto por verdes ou empate)."""
    if not HistoricoRodadas:
        return None
    Ultima = HistoricoRodadas[-1]
    Resultados = {
        R["idJogador"]: int(R.get("verdesMelhor") or 0)
        for R in Ultima.get("resultados") or []
    }
    EuVerdes = Resultados.get(IdObservador, 0)

    if Ultima.get("porVerdes"):
        MaxVerdes = int(Ultima.get("maxVerdes") or 0)
        Ids = Ultima.get("vencedoresRodadaIds") or []
        if MaxVerdes < 1:
            return "Ninguém ficou perto — 0 letras verdes na melhor tentativa."
        if len(Ids) > 1:
            if IdObservador in Ids:
                return (
                    f"Empate! Você ficou na frente com {MaxVerdes} letra(s) verde(s) "
                    f"(sua melhor tentativa: {EuVerdes})."
                )
            return f"Empate — {MaxVerdes} letra(s) verde(s) na melhor tentativa."
        if len(Ids) == 1:
            IdV = Ids[0]
            NomeV = (
                Jogadores[IdV].NomeJogador
                if IdV in Jogadores
                else "Adversário"
            )
            VerdesV = Resultados.get(IdV, 0)
            if IdV == IdObservador:
                Outros = [V for J, V in Resultados.items() if J != IdObservador]
                MelhorOutro = max(Outros) if Outros else 0
                return (
                    f"Você venceu — ficou mais perto da palavra "
                    f"({VerdesV} verde(s) vs {MelhorOutro} do adversário)."
                )
            return (
                f"{NomeV} venceu — ficou mais perto da palavra "
                f"({VerdesV} verde(s) vs {EuVerdes} suas)."
            )
        return None

    IdVencedor = Ultima.get("vencedorRodadaId")
    if IdVencedor and IdVencedor in Jogadores:
        if IdVencedor == IdObservador:
            return "Você acertou a palavra!"
        return f"{Jogadores[IdVencedor].NomeJogador} acertou a palavra."

    if EuVerdes > 0:
        return f"Ninguém acertou. Sua melhor tentativa: {EuVerdes} letra(s) verde(s)."
    return "Ninguém acertou nesta rodada."


def DeterminarCampeaoSessao(Jogadores: dict, Modo: str = ModoPontos) -> str | None:
    if not Jogadores:
        return None
    if Modo == ModoVitorias:
        Melhor = max(
            Jogadores.values(),
            key=lambda J: (getattr(J, "VitoriasRodada", 0), getattr(J, "PontosAcumulados", 0)),
        )
        return Melhor.IdJogador
    Placar = MontarPlacar(Jogadores, Modo)
    return Placar[0]["idJogador"]
