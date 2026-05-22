"""Chat da arena (frases fixas, anti-spam)."""

import time

MaximoMensagensChat = 40

FrasesChatPermitidas = (
    "Boa!",
    "Uau!",
    "Difícil!",
    "Quase!",
    "Gg",
    "Bora",
    "😅",
    "🔥",
    "👏",
    "🎯",
)


def AdicionarMensagemChatSala(Sala, IdJogador: str, Texto: str) -> str | None:
    Jogador = Sala.Jogadores.get(IdJogador)
    if not Jogador:
        return "Jogador inválido."
    Mensagem = (Texto or "").strip()[:80]
    if Mensagem not in FrasesChatPermitidas:
        return "Mensagem não permitida."
    Sala.MensagensChat.append(
        {
            "idJogador": IdJogador,
            "nomeJogador": Jogador.NomeJogador,
            "texto": Mensagem,
            "quando": time.time(),
        }
    )
    if len(Sala.MensagensChat) > MaximoMensagensChat:
        Sala.MensagensChat = Sala.MensagensChat[-MaximoMensagensChat:]
    return None
