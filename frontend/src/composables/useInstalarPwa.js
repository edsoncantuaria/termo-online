import { ref, computed, onMounted, onUnmounted } from "vue";
import {
  AoPromptInstalacaoPronto,
  BarraInstalarMinimizada,
  DefinirBarraInstalarMinimizada,
  DispararPromptInstalacaoAndroid,
  EhInstaladoComoApp,
  PlataformaInstalacao,
  ObterPromptInstalacao,
} from "../utils/pwa-instalar.js";

/**
 * Faixa de instalação PWA (Android: prompt nativo; iOS: Safari / tela de início).
 */
export function useInstalarPwa() {
  const instalado = ref(EhInstaladoComoApp());
  const minimizada = ref(BarraInstalarMinimizada());
  const temPromptAndroid = ref(!!ObterPromptInstalacao());
  const dialogoAberto = ref(false);

  const plataforma = computed(() => PlataformaInstalacao());

  const podeMostrar = computed(() => {
    if (instalado.value) return false;
    return !!plataforma.value && plataforma.value !== "instalado";
  });

  const ehAndroid = computed(() => plataforma.value === "android");
  const ehIosSafari = computed(() => plataforma.value === "ios-safari");
  const ehIosInApp = computed(() => plataforma.value === "ios-inapp");

  const textoPrincipal = computed(() => {
    if (ehAndroid.value) {
      return temPromptAndroid.value
        ? "Instale o Termo como app — abre rápido e funciona melhor offline na prática."
        : "Instale o Termo: no menu do Chrome (⋮), toque em “Instalar app” ou “Adicionar à tela inicial”.";
    }
    if (ehIosSafari.value) {
      return "Adicione à Tela de Início pelo Safari — ícone na home, tela cheia.";
    }
    if (ehIosInApp.value) {
      return "Para instalar, abra esta página no Safari (navegador do iPhone).";
    }
    return "Instale o jogo no seu celular para acesso rápido.";
  });

  const rotuloBotao = computed(() => {
    if (ehAndroid.value && temPromptAndroid.value) return "Instalar jogo";
    if (ehIosSafari.value) return "Como instalar";
    if (ehIosInApp.value) return "Abrir no Safari";
    return "Instalar jogo";
  });

  function atualizarEstado() {
    instalado.value = EhInstaladoComoApp();
    temPromptAndroid.value = !!ObterPromptInstalacao();
  }

  let removerListenerPrompt = null;
  let aoInstalado = null;

  onMounted(() => {
    atualizarEstado();
    removerListenerPrompt = AoPromptInstalacaoPronto(() => {
      temPromptAndroid.value = true;
    });
    aoInstalado = () => {
      instalado.value = true;
      dialogoAberto.value = false;
    };
    window.addEventListener("termo-pwa-instalado", aoInstalado);
    window.addEventListener("visibilitychange", atualizarEstado);
  });

  onUnmounted(() => {
    removerListenerPrompt?.();
    window.removeEventListener("termo-pwa-instalado", aoInstalado);
    window.removeEventListener("visibilitychange", atualizarEstado);
  });

  function minimizar() {
    minimizada.value = true;
    DefinirBarraInstalarMinimizada(true);
    dialogoAberto.value = false;
  }

  function expandir() {
    minimizada.value = false;
    DefinirBarraInstalarMinimizada(false);
  }

  function abrirDialogo() {
    dialogoAberto.value = true;
  }

  function fecharDialogo() {
    dialogoAberto.value = false;
  }

  async function acaoPrincipal() {
    if (ehIosInApp.value) {
      abrirDialogo();
      return;
    }
    if (ehIosSafari.value) {
      abrirDialogo();
      return;
    }
    if (ehAndroid.value && temPromptAndroid.value) {
      const R = await DispararPromptInstalacaoAndroid();
      if (R.ok && R.aceito) instalado.value = true;
      else if (R.motivo === "sem-prompt") abrirDialogo();
      return;
    }
    abrirDialogo();
  }

  async function copiarLinkSafari(mostrarToast) {
    const Url = window.location.href;
    try {
      await navigator.clipboard.writeText(Url);
      mostrarToast?.("Link copiado. Cole no Safari.", false);
    } catch {
      mostrarToast?.(Url, false);
    }
  }

  return {
    podeMostrar,
    minimizada,
    dialogoAberto,
    plataforma,
    ehAndroid,
    ehIosSafari,
    ehIosInApp,
    temPromptAndroid,
    textoPrincipal,
    rotuloBotao,
    minimizar,
    expandir,
    abrirDialogo,
    fecharDialogo,
    acaoPrincipal,
    copiarLinkSafari,
  };
}
