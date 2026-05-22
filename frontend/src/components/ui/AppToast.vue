<script setup>
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
</script>

<template>
  <p
    v-if="store.toast"
    class="toast"
    :class="{
      erro: store.toastErro,
      sucesso: store.toastSucesso,
    }"
    role="status"
  >
    <span v-if="store.toastErro" class="toast-icone" aria-hidden="true">!</span>
    <span v-else-if="store.toastSucesso" class="toast-icone" aria-hidden="true">✓</span>
    {{ store.toast }}
  </p>
</template>
