import { onMounted, onUnmounted, ref } from "vue";

/** `true` quando a viewport é no máximo `px` de largura. */
export function useMediaMax(px = 720) {
  const bate = ref(false);
  let mq = null;

  function Atualizar() {
    bate.value = mq?.matches ?? false;
  }

  onMounted(() => {
    mq = window.matchMedia(`(max-width: ${px}px)`);
    Atualizar();
    mq.addEventListener("change", Atualizar);
  });

  onUnmounted(() => {
    mq?.removeEventListener("change", Atualizar);
  });

  return bate;
}
