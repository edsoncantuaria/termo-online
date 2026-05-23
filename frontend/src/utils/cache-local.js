import {
  CHAVE_SESSAO,
  CHAVE_CODIGO_SALA,
  CHAVE_STATS,
  CHAVE_TUTORIAL_VISTO,
  CHAVE_TUTORIAL_MULTI,
} from "./constantes.js";
import { LimparAuthLocal } from "./auth.js";
import { LimparSessao } from "./sessao.js";

const CHAVE_HASH_DICIONARIO = "termoDicionarioHash";
const CHAVE_PALAVRAS_DICIONARIO = "termoDicionarioPalavras";

/** Remove cache de dicionário, sessão retomável, tutoriais e estatísticas locais. */
export function LimparCacheAplicacao() {
  LimparSessao();
  localStorage.removeItem(CHAVE_HASH_DICIONARIO);
  localStorage.removeItem(CHAVE_PALAVRAS_DICIONARIO);
  localStorage.removeItem(CHAVE_STATS);
  localStorage.removeItem(CHAVE_TUTORIAL_VISTO);
  localStorage.removeItem(CHAVE_TUTORIAL_MULTI);
  localStorage.removeItem(CHAVE_CODIGO_SALA);
}

/** Apaga tudo no navegador (logout, evita retomar partida inválida). */
export function LimparLocalStorageCompleto() {
  try {
    localStorage.clear();
  } catch {
    LimparCacheAplicacao();
    LimparAuthLocal();
  }
}

/** Service worker + Cache API (PWA) — uso ao “Limpar cache local”. */
export async function LimparCachesPwa() {
  if (typeof caches !== "undefined") {
    const Chaves = await caches.keys();
    await Promise.all(Chaves.map((c) => caches.delete(c)));
  }
  if ("serviceWorker" in navigator) {
    const Registros = await navigator.serviceWorker.getRegistrations();
    await Promise.all(Registros.map((r) => r.unregister()));
  }
}
