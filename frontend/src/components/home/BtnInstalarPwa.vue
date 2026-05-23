<script setup>
import { useTermoStore } from "../../stores/termo.js";
import { useInstalarPwa } from "../../composables/useInstalarPwa.js";

const store = useTermoStore();
const { podeMostrar, instalar } = useInstalarPwa();

function aoClicar() {
  instalar((texto, erro, sucesso) => store.mostrarToast(texto, erro, sucesso));
}
</script>

<template>
  <button
    v-if="podeMostrar"
    type="button"
    class="btn-instalar-pwa"
    @click="aoClicar"
  >
    Instalar jogo
  </button>
</template>
