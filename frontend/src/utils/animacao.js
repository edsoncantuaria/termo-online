import { TAMANHO_PALAVRA } from "./constantes.js";

export const DURACAO_FLIP_LINHA =
  TAMANHO_PALAVRA * 180 + 380;

/** Remove flag `animar` após a animação de virada das letras. */
export function AgendarFimAnimacao(alvo, aoTerminar) {
  if (!alvo) return;
  setTimeout(() => {
    if (alvo.animar) alvo.animar = false;
    aoTerminar?.();
  }, DURACAO_FLIP_LINHA);
}
