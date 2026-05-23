/** Monta resumo de jogo ativo a partir do localStorage (visitante ou fallback). */

const RotulosSolo = {
  diaria: "Palavra do dia",
  pratica: "Prática",
  dueto: "Dueto",
  quarteto: "Quarteto",
  desafio: "Desafio",
};

function TextoEstadoLocal(
  tipo,
  estadoSala,
  pausada,
  segundosPausa,
  segundosAbandono,
  souJogadorPausado
) {
  if (pausada) {
    if (souJogadorPausado) {
      const Partes = [];
      if (segundosPausa != null) {
        Partes.push(`Reconecte em até ${segundosPausa}s`);
      }
      if (segundosAbandono != null) {
        Partes.push(`abandono em ${segundosAbandono}s`);
      }
      return Partes.length
        ? `Partida pausada — ${Partes.join(" · ")}`
        : "Partida pausada — reconecte agora";
    }
    return segundosPausa != null
      ? `Oponente desconectou — retoma em ${segundosPausa}s`
      : "Partida pausada — aguardando oponente";
  }
  if (estadoSala === "jogando") {
    return tipo === "ranqueada"
      ? "Rodada em andamento — duelo ranqueado"
      : "Rodada em andamento";
  }
  if (estadoSala === "aguardando") {
    return "Sala aberta — reconecte para continuar";
  }
  return "Partida em andamento";
}

export function JogoAtivoDeSessaoLocal(salvo) {
  if (!salvo) return null;

  if (salvo.ranqueada) {
    const S = salvo.ranqueada;
    return {
      ativo: true,
      tipo: "ranqueada",
      titulo: "Duelo ranqueado",
      codigoSala: S.codigoSala,
      idPartida: S.idPartida,
      idJogador: S.idJogador,
      tokenSessao: S.tokenSessao,
      estadoSala: S.estadoSala || "jogando",
      pausada: !!S.pausada,
      segundosPausaRestantes: S.segundosPausaRestantes ?? null,
      segundosAteAbandono: S.segundosAteAbandono ?? null,
      souJogadorPausado: !!S.souJogadorPausado,
      emTempoDeJogo: S.view === "jogo" && !S.pausada,
      textoEstado: TextoEstadoLocal(
        "ranqueada",
        S.estadoSala,
        S.pausada,
        S.segundosPausaRestantes,
        S.segundosAteAbandono,
        S.souJogadorPausado
      ),
      view: S.view,
    };
  }

  if (salvo.arena) {
    const S = salvo.arena;
    return {
      ativo: true,
      tipo: "arena",
      titulo: "Arena online",
      codigoSala: S.codigoSala,
      idPartida: S.idPartida,
      idJogador: S.idJogador,
      tokenSessao: S.tokenSessao,
      estadoSala: S.estadoSala || "aguardando",
      pausada: !!S.pausada,
      segundosPausaRestantes: S.segundosPausaRestantes ?? null,
      segundosAteAbandono: S.segundosAteAbandono ?? null,
      souJogadorPausado: !!S.souJogadorPausado,
      emTempoDeJogo: S.view === "jogo" && !S.pausada,
      textoEstado: TextoEstadoLocal(
        "arena",
        S.estadoSala,
        S.pausada,
        S.segundosPausaRestantes,
        S.segundosAteAbandono,
        S.souJogadorPausado
      ),
      view: S.view,
    };
  }

  if (salvo.solo) {
    const S = salvo.solo;
    return {
      ativo: true,
      tipo: "solo",
      titulo: RotulosSolo[S.modo] || "Partida solo",
      modoSolo: S.modo,
      idPartida: S.idPartida,
      tokenPartida: S.tokenPartida,
      estadoSala: "jogando",
      pausada: false,
      emTempoDeJogo: true,
      textoEstado: "Partida solo em andamento",
    };
  }

  return null;
}
