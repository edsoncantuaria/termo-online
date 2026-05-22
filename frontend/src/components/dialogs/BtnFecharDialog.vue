<script setup>
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
</script>

<template>
  <button
    type="button"
    class="btn-icone btn-fechar-dialog"
    aria-label="Fechar"
    @click="store.fecharDialogs()"
  >
    ×
  </button>
</template>
