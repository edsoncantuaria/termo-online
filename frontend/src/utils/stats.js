import { CHAVE_STATS } from "./constantes.js";
import { DataDiaServidor, DiariaJaJogadaComDataServidor } from "./tempo-servidor.js";

export function ObterStats() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE_STATS) || "{}");
  } catch {
    return {};
  }
}

export function SalvarStats(S) {
  localStorage.setItem(CHAVE_STATS, JSON.stringify(S));
}

/** @deprecated Use DiariaJaJogadaComDataServidor ou flag `jaJogou` da API. */
export function DiariaJaJogadaLocal() {
  return DiariaJaJogadaComDataServidor(ObterStats(), DataDiaServidor());
}
