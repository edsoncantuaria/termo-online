/** Estilo visual do nível (anel do avatar). */
export function EstiloNivelCss(estilo) {
  if (!estilo) return {};
  return {
    "--anel-cor1": estilo.cor1,
    "--anel-cor2": estilo.cor2,
    "--anel-borda": `${estilo.bordaPx || 2}px`,
  };
}

export function TextoXpGanho(progresso) {
  if (progresso?.xpCapAtingido && !progresso?.xpGanho) {
    return "Limite diário de XP atingido — volta amanhã";
  }
  if (!progresso?.xpGanho) return "";
  let t = `+${progresso.xpGanho} XP`;
  const pct =
    progresso.progresso?.multiplicadorXpPct ??
    progresso.multiplicadorXpPct;
  if (progresso.xpBruto && progresso.xpBruto > progresso.xpGanho) {
    t += ` (${progresso.xpBruto} base`;
    if (pct != null) t += ` · ${pct}% no nível`;
    t += ")";
  } else if (pct != null && pct < 100) {
    t += ` · ${pct}% no nível`;
  }
  if (progresso.subiuNivel) t += " · Subiu de nível!";
  return t;
}

/** Barras simples para histórico 7d (altura 0–100). */
export function BarrasHistorico7d(historico) {
  if (!historico?.dias?.length) return [];
  const maxXp = Math.max(1, ...(historico.xp || []));
  const maxRp = Math.max(1, ...(historico.deltaRp || []).map((v) => Math.abs(v)));
  return historico.dias.map((dia, i) => ({
    dia: dia.slice(5),
    xp: historico.xp[i] || 0,
    deltaRp: historico.deltaRp[i] || 0,
    alturaXp: Math.round((100 * (historico.xp[i] || 0)) / maxXp),
    alturaRp: Math.round((100 * Math.abs(historico.deltaRp[i] || 0)) / maxRp),
  }));
}
