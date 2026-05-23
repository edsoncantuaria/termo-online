/** Modos que usam salas online (WebSocket), distintos do solo. */
export function EhModoSalaOnline(Modo) {
  return Modo === "arena" || Modo === "ranqueada";
}

/** Partida pendente que exige reconexão e bloqueia outros modos (arena/ranqueada). */
export function EhJogoAtivoOnline(J) {
  return J?.ativo && (J.tipo === "arena" || J.tipo === "ranqueada");
}

/** Duelo ranqueado em andamento (qualquer tela — exige desistir para sair com penalidade). */
export function PartidaRanqueadaAtiva(Estado) {
  return (
    Estado.modo === "ranqueada" &&
    !!Estado.idPartida &&
    !!Estado.idJogador &&
    !Estado.espectador &&
    !Estado.dadosSala?.partidaEncerrada
  );
}

const ESTADOS_ARENA_ATIVOS = new Set([
  "jogando",
  "countdown",
  "entre_rodadas",
  "pausada",
]);

/** Arena com partida em curso — logout/voltar deve desistir, não só sair da sala. */
export function PartidaArenaEmRodada(Estado) {
  if (
    Estado.modo !== "arena" ||
    !Estado.idPartida ||
    !Estado.idJogador ||
    Estado.espectador ||
    Estado.dadosSala?.partidaEncerrada
  ) {
    return false;
  }
  const Est = Estado.dadosSala?.estadoSala || Estado.estadoSalaArena;
  return Estado.view === "jogo" || (Est && ESTADOS_ARENA_ATIVOS.has(Est));
}
