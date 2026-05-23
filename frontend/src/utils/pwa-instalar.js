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

export function EhAndroid() {
  return /android/i.test(navigator.userAgent);
}

export function EhIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

/** Safari no iOS (não Chrome/Firefox/Edge no iPhone). */
export function EhIosSafari() {
  if (!EhIos()) return false;
  const Ua = navigator.userAgent;
  if (/crios|fxios|edgios|opr\//i.test(Ua)) return false;
  return /safari/i.test(Ua);
}

/** Instagram, Facebook, etc. — precisa abrir no Safari. */
export function EhIosNavegadorEmbutido() {
  return EhIos() && !EhIosSafari();
}

export function EhMobileOuTablet() {
  return EhAndroid() || EhIos();
}

export function PlataformaInstalacao() {
  if (EhInstaladoComoApp()) return "instalado";
  if (EhIosNavegadorEmbutido()) return "ios-inapp";
  if (EhIosSafari()) return "ios-safari";
  if (EhAndroid()) return "android";
  if (EhIos()) return "ios-outro";
  return null;
}

export function UrlAbrirNoSafari() {
  return window.location.href;
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
