<script setup>
import { computed, onMounted, onUnmounted } from "vue";
import { useTermoStore } from "./stores/termo.js";
import AppTopo from "./components/layout/AppTopo.vue";
import ViewInicio from "./components/views/ViewInicio.vue";
import ViewArenaLobby from "./components/views/ViewArenaLobby.vue";
import ViewJogo from "./components/views/ViewJogo.vue";
import DialogPerfil from "./components/dialogs/DialogPerfil.vue";
import DialogJogar from "./components/dialogs/DialogJogar.vue";
import DialogCriarSala from "./components/dialogs/DialogCriarSala.vue";
import DialogAjuda from "./components/dialogs/DialogAjuda.vue";
import DialogAviso from "./components/dialogs/DialogAviso.vue";
import DialogResultado from "./components/dialogs/DialogResultado.vue";
import DialogConta from "./components/dialogs/DialogConta.vue";
import AppToast from "./components/ui/AppToast.vue";
import TutorialPrimeiraVisita from "./components/ui/TutorialPrimeiraVisita.vue";

const store = useTermoStore();

const classesApp = computed(() => ({
  "app-desktop": true,
  "modo-jogo": store.emJogo,
  "modo-jogo-multi": store.emJogo && store.modoMulti,
  "modo-jogo-arena": store.modoJogoArena,
  "modo-jogo-ranqueada": store.modoJogoRanqueada,
  "modo-sala-espera": store.emLobby,
}));

function onKeydown(e) {
  if (store.view !== "jogo" || store.encerrada) return;
  if (e.key === "Enter") store.onTecla("enter");
  else if (e.key === "Backspace") store.onTecla("back");
  else if (/^[a-zA-Z]$/.test(e.key)) store.onTecla(e.key.toLowerCase());
}

function onEscape(e) {
  if (e.key !== "Escape" || !store.dialogAberto) return;
  store.fecharDialogs();
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
  document.addEventListener("keydown", onEscape);
  store.inicializar();
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("keydown", onEscape);
});
</script>

<template>
  <div class="aurora" aria-hidden="true" />
  <div
    v-if="store.bannerReconexao"
    class="banner-reconexao"
    role="status"
    aria-live="polite"
  >
    Reconectando…
  </div>

  <div class="app" :class="classesApp">
    <AppTopo />
    <main class="principal">
      <ViewInicio v-if="store.view === 'inicio'" />
      <ViewArenaLobby v-else-if="store.view === 'arenaLobby'" />
      <ViewJogo v-else-if="store.view === 'jogo'" />
    </main>
    <AppToast />
  </div>

  <DialogPerfil />
  <DialogConta />
  <DialogJogar />
  <DialogCriarSala />
  <DialogAjuda />
  <DialogAviso />
  <DialogResultado />
  <TutorialPrimeiraVisita
    v-if="store.mostrarTutorial"
    @fechar="store.fecharTutorial()"
  />
</template>

<style>
@import "./assets/estilo.css";
@import "./assets/polish.css";
@import "./assets/tema-claro.css";
</style>
