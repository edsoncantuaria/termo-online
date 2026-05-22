import { watch, onBeforeUnmount } from "vue";

/**
 * Sincroniza um <dialog> com estado reativo via showModal()/close().
 */
export function useDialogoNativo(elRef, abertoRef, aoFechar) {
  const fechar = () => aoFechar?.();

  const Sincronizar = (visivel) => {
    const el = elRef.value;
    if (!el) return;
    if (visivel) {
      if (!el.open) {
        try {
          el.showModal();
        } catch {
          el.show();
        }
      }
    } else if (el.open) {
      el.close();
    }
  };

  watch(abertoRef, Sincronizar, { flush: "post", immediate: true });

  onBeforeUnmount(() => {
    const el = elRef.value;
    if (el?.open) el.close();
  });

  /** Clique no backdrop (alvo é o próprio <dialog>). */
  function onCliqueFora(ev) {
    if (ev.target === elRef.value) fechar();
  }

  /** Escape ou clique fora (evento cancel do UA). */
  function onCancel(ev) {
    ev.preventDefault();
    fechar();
  }

  return { fechar, onCliqueFora, onCancel };
}
