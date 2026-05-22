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
  if (progresso.subiuNivel) t += " · Subiu de nível!";
  return t;
}
