/**
 * Mensagens de pressão na série (arena / ranqueada — primeiro a N vitórias).
 * @returns {{ texto: string, tipo: string } | null}
 */
export function CalcularInstigacaoSerie({ vitoriasEu, vitoriasOpp, meta }) {
  const Meta = Math.max(1, Number(meta) || 1);
  const Eu = Math.max(0, Number(vitoriasEu) || 0);
  const Opp = Math.max(0, Number(vitoriasOpp) || 0);
  const FaltaEu = Meta - Eu;
  const FaltaOpp = Meta - Opp;

  if (FaltaEu <= 0 || FaltaOpp <= 0) return null;

  if (FaltaEu === 1 && FaltaOpp === 1) {
    return {
      texto: "Mapa decisivo — quem vencer leva a série!",
      tipo: "decisivo",
    };
  }
  if (FaltaEu === 1) {
    return {
      texto: "Se ganhar esta, vence a partida!",
      tipo: "vantagem",
    };
  }
  if (FaltaOpp === 1) {
    return {
      texto: "Precisa ganhar esta para continuar na partida!",
      tipo: "pressionado",
    };
  }
  return null;
}

/** Chave estável para não repetir o mesmo toast na rodada. */
export function ChaveInstigacaoSerie(inst, vitoriasEu, vitoriasOpp) {
  if (!inst) return null;
  return `${inst.tipo}:${vitoriasEu}:${vitoriasOpp}`;
}
