/** Estado global da atualização do service worker (PWA). */
import { ref } from "vue";

export const atualizacaoPwaDisponivel = ref(false);

let aplicarAtualizacaoFn = null;

export function registrarAplicarAtualizacaoPwa(fn) {
  aplicarAtualizacaoFn = fn;
}

export async function aplicarAtualizacaoPwa() {
  if (!aplicarAtualizacaoFn) {
    window.location.reload();
    return;
  }
  await aplicarAtualizacaoFn(true);
}
