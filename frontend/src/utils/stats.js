import { CHAVE_STATS } from "./constantes.js";

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

export function DiariaJaJogadaLocal() {
  const s = ObterStats();
  return s.ultimaDiaria === new Date().toISOString().slice(0, 10);
}
