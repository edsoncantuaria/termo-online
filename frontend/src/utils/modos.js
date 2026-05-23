/** Modos que usam salas online (WebSocket), distintos do solo. */
export function EhModoSalaOnline(Modo) {
  return Modo === "arena" || Modo === "ranqueada";
}

/** Partida pendente que exige reconexão e bloqueia outros modos (arena/ranqueada). */
export function EhJogoAtivoOnline(J) {
  return J?.ativo && (J.tipo === "arena" || J.tipo === "ranqueada");
}
