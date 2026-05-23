/** Textos e contagem para hero / bloqueio de partida pendente. */

export function TextoContagemHero(J, { pausaRestante, abandonoRestante }) {
  if (!J?.ativo) return "";
  const Tipo = J.tipo;
  if (Tipo === "solo") {
    return J.textoEstado || "Partida em andamento — continue quando quiser.";
  }
  const Pausa = pausaRestante ?? J.segundosPausaRestantes;
  const Abandono = abandonoRestante ?? J.segundosAteAbandono;

  if (J.pausada) {
    if (J.souJogadorPausado) {
      const Partes = [];
      if (Pausa != null && Pausa > 0) {
        Partes.push(
          `Reconecte em até ${formatarSeg(Pausa)} antes da partida seguir sem você`
        );
      }
      if (Abandono != null && Abandono > 0) {
        Partes.push(
          `Derrota por abandono em ${formatarSeg(Abandono)} se não voltar`
        );
      }
      return Partes.join(". ") || J.textoEstado || "Partida pausada — reconecte agora.";
    }
    const Partes = [
      "Oponente desconectou",
    ];
    if (Pausa != null && Pausa > 0) {
      Partes.push(`a partida retoma em ${formatarSeg(Pausa)}`);
    }
    if (Abandono != null && Abandono > 0 && (Tipo === "ranqueada" || Tipo === "arena")) {
      Partes.push(`vitória por abandono dele em ${formatarSeg(Abandono)}`);
    }
    return `${Partes.join(" · ")}.`;
  }

  if (Tipo === "ranqueada" || Tipo === "arena") {
    return (
      J.textoEstado ||
      "Partida em andamento — reconecte para não prejudicar o oponente."
    );
  }
  return J.textoEstado || "Partida em andamento.";
}

export function TextoBloqueioNovoModo(J, { pausaRestante, abandonoRestante }) {
  if (!J?.ativo) return "";
  const Corpo = TextoContagemHero(J, { pausaRestante, abandonoRestante });
  return `${Corpo} Não é possível iniciar outro modo até reconectar ou abandonar esta partida.`;
}

function formatarSeg(Seg) {
  const N = Math.max(0, Math.floor(Number(Seg) || 0));
  if (N >= 60) {
    const M = Math.floor(N / 60);
    const S = N % 60;
    return S > 0 ? `${M} min ${S}s` : `${M} min`;
  }
  return `${N}s`;
}

export function DecrementarContagens(J) {
  if (!J?.ativo) return { pausa: null, abandono: null };
  const pausa =
    J.segundosPausaRestantes != null
      ? Math.max(0, J.segundosPausaRestantes - 1)
      : null;
  const abandono =
    J.segundosAteAbandono != null
      ? Math.max(0, J.segundosAteAbandono - 1)
      : null;
  return { pausa, abandono };
}
