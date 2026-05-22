/** Modos que usam salas online (WebSocket), distintos do solo. */
export function EhModoSalaOnline(Modo) {
  return Modo === "arena" || Modo === "ranqueada";
}
