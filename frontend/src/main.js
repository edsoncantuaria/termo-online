import { createApp } from "vue";
import { createPinia } from "pinia";
import { registerSW } from "virtual:pwa-register";
import App from "./App.vue";
import { desbloquearAudio, prepararSons } from "./lib/som.js";

if (import.meta.env.PROD) {
  const IntervaloChecagemMs = 5 * 60 * 1000;
  registerSW({
    immediate: true,
    onRegisteredSW(_swUrl, registration) {
      if (!registration) return;
      const ChecarAtualizacao = () => {
        if (!navigator.onLine || registration.installing) return;
        registration.update().catch(() => {});
      };
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") ChecarAtualizacao();
      });
      setInterval(ChecarAtualizacao, IntervaloChecagemMs);
    },
  });
}

const app = createApp(App);
app.use(createPinia());
app.mount("#app");

prepararSons();
for (const ev of ["pointerdown", "keydown", "touchstart"]) {
  document.addEventListener(ev, desbloquearAudio, { once: true, passive: true });
}
