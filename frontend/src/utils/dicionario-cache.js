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

export function SalvarCacheDicionario(hash, palavras) {
  localStorage.setItem(CHAVE_HASH, hash);
  localStorage.setItem(CHAVE_PALAVRAS, JSON.stringify([...palavras]));
}

export function PalavraNoCache(palavra, conjunto) {
  if (!conjunto || !(conjunto instanceof Set)) return null;
  return conjunto.has(palavra);
}
