import { ref, computed, onMounted, onUnmounted } from "vue";

function EhMobile() {
  return /android|iphone|ipad|ipod/i.test(navigator.userAgent);
}

function EhIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

function EhInstalado() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

/**
 * Prompt de instalação PWA (Android/Chrome) e dica discreta no iOS.
 */
export function useInstalarPwa() {
  const promptEvento = ref(null);
  const instalado = ref(EhInstalado());

  const podeMostrar = computed(() => {
    if (!EhMobile() || instalado.value) return false;
    if (promptEvento.value) return true;
    return EhIos();
  });

  let handler = null;

  onMounted(() => {
    instalado.value = EhInstalado();
    handler = (e) => {
      e.preventDefault();
      promptEvento.value = e;
    };
    window.addEventListener("beforeinstallprompt", handler);
  });

  onUnmounted(() => {
    if (handler) {
      window.removeEventListener("beforeinstallprompt", handler);
    }
  });

  async function instalar(mostrarToast) {
    if (EhIos()) {
      mostrarToast?.(
        "No Safari: toque em Compartilhar e escolha “Adicionar à Tela de Início”.",
        false,
        false
      );
      return;
    }
    const Ev = promptEvento.value;
    if (!Ev) return;
    await Ev.prompt();
    const { outcome } = await Ev.userChoice;
    if (outcome === "accepted") {
      instalado.value = true;
      promptEvento.value = null;
    }
  }

  return { podeMostrar, instalar };
}
