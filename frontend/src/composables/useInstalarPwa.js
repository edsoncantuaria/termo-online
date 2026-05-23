import { ref, computed, onMounted, onUnmounted, watch, unref } from "vue";
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
 * @param {import('vue').Ref<boolean>|import('vue').ComputedRef<boolean>|(() => boolean)} EstaNoMenuPrincipal
 */
export function useInstalarPwa(EstaNoMenuPrincipal = ref(true)) {
  const instalado = ref(EhInstaladoComoApp());
  const minimizada = ref(BarraInstalarMinimizada());
  const temPromptAndroid = ref(!!ObterPromptInstalacao());
  const dialogoAberto = ref(false);

  const plataforma = computed(() => PlataformaInstalacao());

  const noMenuPrincipal = computed(() => !!unref(EstaNoMenuPrincipal));

  const podeInstalar = computed(() => {
    if (instalado.value) return false;
    const P = plataforma.value;
    return !!P && P !== "instalado";
  });

  /** Só na home — nunca em partida, arena ou diálogos de jogo. */
  const podeMostrar = computed(
    () => noMenuPrincipal.value && podeInstalar.value
  );

  const ehAndroid = computed(() => plataforma.value === "android");
  const ehIosSafari = computed(() => plataforma.value === "ios-safari");
  const ehIosInApp = computed(() => plataforma.value === "ios-inapp");

  const textoPrincipal = computed(() => {
    if (ehAndroid.value) {
      return temPromptAndroid.value
        ? "Instale o Termo como app — abre rápido na tela inicial."
        : "Instale o Termo: menu ⋮ do Chrome → Instalar app ou Adicionar à tela inicial.";
    }
    if (ehIosSafari.value) {
      return "Adicione à Tela de Início pelo Safari — ícone na home, tela cheia.";
    }
    if (ehIosInApp.value) {
      return "Para instalar, abra esta página no Safari (navegador do iPhone).";
    }
    return "Instale o jogo no celular para acesso rápido.";
  });

  const rotuloBotao = computed(() => {
    if (ehAndroid.value && temPromptAndroid.value) return "Instalar jogo";
    if (ehIosSafari.value) return "Como instalar";
    if (ehIosInApp.value) return "Ver como instalar";
    return "Como instalar";
  });

  function atualizarEstado() {
    instalado.value = EhInstaladoComoApp();
    temPromptAndroid.value = !!ObterPromptInstalacao();
  }

  let removerListenerPrompt = null;
  let aoInstalado = null;
  let aoEscape = null;

  function fecharDialogo() {
    dialogoAberto.value = false;
  }

  function abrirDialogo() {
    if (!podeInstalar.value) return;
    dialogoAberto.value = true;
  }

  onMounted(() => {
    atualizarEstado();
    removerListenerPrompt = AoPromptInstalacaoPronto(() => {
      temPromptAndroid.value = true;
    });
    aoInstalado = () => {
      instalado.value = true;
      fecharDialogo();
    };
    window.addEventListener("termo-pwa-instalado", aoInstalado);
    window.addEventListener("visibilitychange", atualizarEstado);

    aoEscape = (e) => {
      if (e.key === "Escape" && dialogoAberto.value) {
        e.stopPropagation();
        fecharDialogo();
      }
    };
    window.addEventListener("keydown", aoEscape, true);
  });

  onUnmounted(() => {
    removerListenerPrompt?.();
    window.removeEventListener("termo-pwa-instalado", aoInstalado);
    window.removeEventListener("visibilitychange", atualizarEstado);
    window.removeEventListener("keydown", aoEscape, true);
  });

  watch(noMenuPrincipal, (NoMenu) => {
    if (!NoMenu) fecharDialogo();
  });

  function minimizar() {
    minimizada.value = true;
    DefinirBarraInstalarMinimizada(true);
    fecharDialogo();
  }

  function expandir() {
    minimizada.value = false;
    DefinirBarraInstalarMinimizada(false);
  }

  async function acaoPrincipal() {
    if (!podeMostrar.value) return;

    if (ehAndroid.value && temPromptAndroid.value) {
      const R = await DispararPromptInstalacaoAndroid();
      if (R.ok && R.aceito) instalado.value = true;
      else if (R.motivo === "sem-prompt") abrirDialogo();
      return;
    }

    if (ehIosSafari.value || ehIosInApp.value) {
      abrirDialogo();
      return;
    }

    if (ehAndroid.value) {
      abrirDialogo();
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
    podeInstalar,
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
