/** Data/hora oficiais do servidor (Brasília) — não usar relógio local para diária. */
import { UrlApi } from "../config/origem.js";
import { fetchPublicoJson } from "../services/api.js";

let cache = {
  dataDiaBrasil: null,
  segundosAteMeiaNoite: null,
  sincronizadoEm: 0,
};

export function DataDiaServidor() {
  return cache.dataDiaBrasil;
}

export function SegundosAteMeiaNoiteServidor() {
  return cache.segundosAteMeiaNoite;
}

export function AplicarTempoServidor(Dados) {
  if (!Dados?.dataDiaBrasil) return;
  cache.dataDiaBrasil = Dados.dataDiaBrasil;
  cache.segundosAteMeiaNoite =
    Dados.segundosAteMeiaNoiteBrasil ?? cache.segundosAteMeiaNoite;
  cache.sincronizadoEm = Date.now();
}

/** Sincroniza com GET /api/tempo (ou /api/health). */
export async function SincronizarTempoServidor() {
  try {
    const D = await fetchPublicoJson(UrlApi("/api/tempo"));
    AplicarTempoServidor(D);
    return D;
  } catch {
    return null;
  }
}

/** Diária já jogada conforme stats locais + data do servidor (nunca relógio do aparelho). */
export function DiariaJaJogadaComDataServidor(stats, dataDiaServidor) {
  const Data = dataDiaServidor || cache.dataDiaBrasil;
  if (!Data || !stats?.ultimaDiaria) return false;
  return stats.ultimaDiaria === Data;
}
