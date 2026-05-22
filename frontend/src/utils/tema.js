/** Tema: claro, escuro ou seguir o sistema. */

export function ResolverTemaClaro(preferencias) {
  const modo = preferencias?.temaModo || "sistema";
  if (modo === "claro") return true;
  if (modo === "escuro") return false;
  return !window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function AplicarTemaPreferencias(preferencias) {
  const claro = ResolverTemaClaro(preferencias);
  document.documentElement.classList.toggle("tema-claro", claro);
  return claro;
}

export function ObservarTemaSistema(callback) {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const fn = () => callback();
  mq.addEventListener("change", fn);
  return () => mq.removeEventListener("change", fn);
}
