import { UrlApi } from "../config/origem.js";
import { fetchPublicoJson } from "../services/api.js";

const CHAVE_HASH = "termoDicionarioHash";
const CHAVE_PALAVRAS = "termoDicionarioPalavras";

export function LimparCacheDicionario() {
  localStorage.removeItem(CHAVE_HASH);
  localStorage.removeItem(CHAVE_PALAVRAS);
}

export async function CarregarCacheDicionario() {
  try {
    const Info = await fetchPublicoJson(UrlApi("/api/dicionario/info"));
    const HashLocal = localStorage.getItem(CHAVE_HASH);
    if (HashLocal === Info.hash) {
      const Raw = localStorage.getItem(CHAVE_PALAVRAS);
      if (Raw) return new Set(JSON.parse(Raw));
    }
    return { hash: Info.hash, precisaBaixar: true };
  } catch {
    return null;
  }
}

export async function GarantirCacheDicionario() {
  const cache = await CarregarCacheDicionario();
  if (cache instanceof Set) return cache;
  if (!cache?.precisaBaixar) return null;
  try {
    const D = await fetchPublicoJson(UrlApi("/api/dicionario/palavras"));
    const conjunto = new Set(D.palavras || []);
    if (conjunto.size > 0) {
      SalvarCacheDicionario(D.hash, conjunto);
    }
    return conjunto.size > 0 ? conjunto : null;
  } catch {
    return null;
  }
}

export function SalvarCacheDicionario(hash, palavras) {
  localStorage.setItem(CHAVE_HASH, hash);
  localStorage.setItem(CHAVE_PALAVRAS, JSON.stringify([...palavras]));
}

export function PalavraNoCache(palavra, conjunto) {
  if (!conjunto || !(conjunto instanceof Set)) return null;
  return conjunto.has(palavra);
}
