import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { desbloquearAudio, prepararSons } from "./lib/som.js";

const app = createApp(App);
app.use(createPinia());
app.mount("#app");

prepararSons();
for (const ev of ["pointerdown", "keydown", "touchstart"]) {
  document.addEventListener(ev, desbloquearAudio, { once: true, passive: true });
}
