import {
  EhModoSalaOnline,
  PartidaArenaEmRodada,
  PartidaRanqueadaAtiva,
} from "./modos.js";

let promessaRetomarSessao = null;
let promessaCarregarJogoAtivo = null;

/** Partida arena/ranqueada em curso nesta aba — evita retomar por storage de outra aba. */
export function PartidaOnlineEmJogo(Estado) {
  if (!EhModoSalaOnline(Estado?.modo) || !Estado.codigoSala || !Estado.idJogador) {
    return false;
  }
  if (Estado.view === "jogo") return true;
  return PartidaRanqueadaAtiva(Estado) || PartidaArenaEmRodada(Estado);
}

export function DeveIgnorarSincronizacaoOutraAba(Estado) {
  return (
    PartidaOnlineEmJogo(Estado) ||
    (Estado.view === "jogo" && !!Estado.carregandoChute)
  );
}

/** Uma retomada por vez (boot, storage, BroadcastChannel). */
export function SolicitarRetomarSessao(executar) {
  if (promessaRetomarSessao) return promessaRetomarSessao;
  promessaRetomarSessao = Promise.resolve()
    .then(executar)
    .finally(() => {
      promessaRetomarSessao = null;
    });
  return promessaRetomarSessao;
}

/** Evita corridas entre boot, visibility e tick do hero. */
export function SerializarCarregarJogoAtivo(executar) {
  if (promessaCarregarJogoAtivo) return promessaCarregarJogoAtivo;
  promessaCarregarJogoAtivo = Promise.resolve()
    .then(executar)
    .finally(() => {
      promessaCarregarJogoAtivo = null;
    });
  return promessaCarregarJogoAtivo;
}

export function CodigoConviteConflita(Estado, codigoConvite) {
  const Convite = (codigoConvite || "").trim().toUpperCase();
  if (!Convite) return false;
  const Atual = (Estado.codigoSala || "").toUpperCase();
  if (!PartidaOnlineEmJogo(Estado)) return false;
  return Atual && Atual !== Convite;
}
