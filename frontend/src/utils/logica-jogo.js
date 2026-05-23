/**
 * Lógica do Termo (espelho de nucleo/logica_jogo.py) — uso offline na prática.
 */
import { TAMANHO_PALAVRA } from "./constantes.js";
import {
  MontarPalavraChute,
  PalavraDeTentativa,
  ValidarModoDificilClient,
} from "./jogo.js";

export const MAXIMO_TENTATIVAS = 6;

export function NormalizarPalavra(Palavra) {
  return (Palavra || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function PalavraJaFoiTentada(Tentativas, PalavraNormalizada) {
  const Alvo = NormalizarPalavra(PalavraNormalizada);
  if (!Alvo) return false;
  return (Tentativas || []).some((T) => PalavraDeTentativa(T) === Alvo);
}

/**
 * @param {Set<string>} ConjuntoDicionario
 */
export function PalavraExisteNoDicionario(PalavraNormalizada, ConjuntoDicionario) {
  return !!ConjuntoDicionario?.has(PalavraNormalizada);
}

export function ValidarPalavra(
  Palavra,
  TentativasAnteriores,
  ConjuntoDicionario,
  ModoDificil = false
) {
  const PalavraNormalizada = NormalizarPalavra(Palavra);

  if (PalavraNormalizada.length !== TAMANHO_PALAVRA) {
    return { valido: false, mensagem: "A palavra deve ter exatamente 5 letras." };
  }

  if (!PalavraExisteNoDicionario(PalavraNormalizada, ConjuntoDicionario)) {
    return { valido: false, mensagem: "Palavra não encontrada no dicionário." };
  }

  if (PalavraJaFoiTentada(TentativasAnteriores, PalavraNormalizada)) {
    return { valido: false, mensagem: "Você já tentou essa palavra." };
  }

  if (ModoDificil && TentativasAnteriores?.length) {
    const { ok, msg } = ValidarModoDificilClient(
      PalavraNormalizada,
      TentativasAnteriores
    );
    if (!ok) return { valido: false, mensagem: msg };
  }

  return { valido: true, palavra: PalavraNormalizada };
}

/** Mesma regra do servidor (verdes → amarelos → cinzas). */
export function AvaliarChute(PalavraSecreta, PalavraChute) {
  const LetrasSecretas = [...NormalizarPalavra(PalavraSecreta)];
  const LetrasChute = [...NormalizarPalavra(PalavraChute)];
  const Resultado = Array(TAMANHO_PALAVRA).fill("ausente");

  for (let Indice = 0; Indice < TAMANHO_PALAVRA; Indice++) {
    if (LetrasChute[Indice] === LetrasSecretas[Indice]) {
      Resultado[Indice] = "correto";
      LetrasSecretas[Indice] = null;
      LetrasChute[Indice] = null;
    }
  }

  for (let Indice = 0; Indice < TAMANHO_PALAVRA; Indice++) {
    if (!LetrasChute[Indice]) continue;
    const Posicao = LetrasSecretas.indexOf(LetrasChute[Indice]);
    if (Posicao !== -1) {
      Resultado[Indice] = "presente";
      LetrasSecretas[Posicao] = null;
    }
  }

  return Resultado;
}

export function PalavraFoiAcertada(PalavraSecreta, PalavraChute) {
  return NormalizarPalavra(PalavraSecreta) === NormalizarPalavra(PalavraChute);
}

export function MontarTentativaLocal(PalavraSecreta, PalavraChute) {
  const Estados = AvaliarChute(PalavraSecreta, PalavraChute);
  const Norm = NormalizarPalavra(PalavraChute);
  const Letras = [...Norm.toUpperCase()];
  while (Letras.length < TAMANHO_PALAVRA) Letras.push("");
  return { letras: Letras, estados: Estados, palavra: Norm };
}

/** Sorteia palavra de 5 letras do dicionário em cache. */
export function EscolherPalavraAleatoria(ConjuntoDicionario) {
  if (!ConjuntoDicionario?.size) return null;
  const Lista = [...ConjuntoDicionario];
  return Lista[Math.floor(Math.random() * Lista.length)];
}

export function EhIdPartidaPraticaLocal(IdPartida) {
  return typeof IdPartida === "string" && IdPartida.startsWith("local-pratica-");
}
