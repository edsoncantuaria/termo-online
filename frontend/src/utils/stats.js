import { CHAVE_STATS } from "./constantes.js";
import { DataHojeIsoBrasil } from "./tempo-brasil.js";

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
  return s.ultimaDiaria === DataHojeIsoBrasil();
}
