const CHAVE_HASH = "termoDicionarioHash";
const CHAVE_PALAVRAS = "termoDicionarioPalavras";

export async function CarregarCacheDicionario() {
  try {
    const R = await fetch("/api/dicionario/info");
    if (!R.ok) return null;
    const Info = await R.json();
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
    const R = await fetch("/api/dicionario/palavras");
    if (!R.ok) return null;
    const D = await R.json();
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
