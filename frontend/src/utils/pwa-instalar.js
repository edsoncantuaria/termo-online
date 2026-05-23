/** Detecção de ambiente e prompt global de instalação PWA. */

/** @type {BeforeInstallPromptEvent | null} */
let PromptInstalacaoGlobal = null;

const OUVINTES_PROMPT = new Set();

if (typeof window !== "undefined") {
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    PromptInstalacaoGlobal = e;
    OUVINTES_PROMPT.forEach((Fn) => Fn(e));
  });

  window.addEventListener("appinstalled", () => {
    PromptInstalacaoGlobal = null;
    window.dispatchEvent(new Event("termo-pwa-instalado"));
  });
}

export function ObterPromptInstalacao() {
  return PromptInstalacaoGlobal;
}

export function AoPromptInstalacaoPronto(Callback) {
  if (PromptInstalacaoGlobal) Callback(PromptInstalacaoGlobal);
  OUVINTES_PROMPT.add(Callback);
  return () => OUVINTES_PROMPT.delete(Callback);
}

export function EhInstaladoComoApp() {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    window.navigator.standalone === true
  );
}

function UserAgent() {
  return typeof navigator !== "undefined" ? navigator.userAgent : "";
}

/** iPhone, iPad (incl. iPadOS com UA de Mac) e iPod. */
export function EhIos() {
  const Ua = UserAgent();
  if (/iphone|ipad|ipod/i.test(Ua)) return true;
  return (
    typeof navigator !== "undefined" &&
    navigator.platform === "MacIntel" &&
    navigator.maxTouchPoints > 1
  );
}

export function EhAndroid() {
  const Ua = UserAgent();
  if (/android/i.test(Ua)) return true;
  const Dados = navigator.userAgentData;
  if (Dados?.platform && /android/i.test(Dados.platform)) return true;
  return false;
}

/** Safari no iOS (não Chrome, Firefox, Edge, Opera, WebViews de apps). */
export function EhIosSafari() {
  if (!EhIos()) return false;
  const Ua = UserAgent();
  if (/crios|fxios|edgios|edg\/|opr\/|opt\/|gsa\//i.test(Ua)) return false;
  if (/fbav|fban|fbios|instagram|line\/|twitter|linkedinapp|wv\)/i.test(Ua)) {
    return false;
  }
  if (/safari/i.test(Ua)) return true;
  return !window.chrome && !/crios/i.test(Ua);
}

/** Instagram, Facebook, Chrome no iPhone, etc. */
export function EhIosNavegadorEmbutido() {
  return EhIos() && !EhIosSafari();
}

export function EhMobileOuTablet() {
  return EhAndroid() || EhIos();
}

/**
 * @returns {"instalado"|"ios-safari"|"ios-inapp"|"android"|"ios-outro"|null}
 */
export function PlataformaInstalacao() {
  if (EhInstaladoComoApp()) return "instalado";
  if (EhIosNavegadorEmbutido()) return "ios-inapp";
  if (EhIosSafari()) return "ios-safari";
  if (EhAndroid()) return "android";
  if (EhIos()) return "ios-outro";
  return null;
}

export async function DispararPromptInstalacaoAndroid() {
  const Ev = PromptInstalacaoGlobal;
  if (!Ev) return { ok: false, motivo: "sem-prompt" };
  await Ev.prompt();
  const { outcome } = await Ev.userChoice;
  if (outcome === "accepted") {
    PromptInstalacaoGlobal = null;
    return { ok: true, aceito: true };
  }
  return { ok: true, aceito: false };
}

const CHAVE_MINIMIZAR = "termoPwaBarMinimizada";

export function BarraInstalarMinimizada() {
  try {
    return localStorage.getItem(CHAVE_MINIMIZAR) === "1";
  } catch {
    return false;
  }
}

export function DefinirBarraInstalarMinimizada(Minimizada) {
  try {
    if (Minimizada) localStorage.setItem(CHAVE_MINIMIZAR, "1");
    else localStorage.removeItem(CHAVE_MINIMIZAR);
  } catch {
    /* ignore */
  }
}
