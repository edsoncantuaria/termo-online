<script setup>
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
</script>

<template>
  <!-- Dentro do <dialog> aberto: mesma top layer, sem bloquear a página -->
  <Teleport v-if="store.toast && store.dialogAberto" to="dialog[open]">
    <p
      class="toast toast-em-dialog"
      :class="{
        erro: store.toastErro,
        sucesso: store.toastSucesso,
      }"
      role="alert"
      aria-live="assertive"
    >
      <span v-if="store.toastErro" class="toast-icone" aria-hidden="true">!</span>
      <span v-else-if="store.toastSucesso" class="toast-icone" aria-hidden="true">✓</span>
      {{ store.toast }}
    </p>
  </Teleport>

  <p
    v-else-if="store.toast"
    class="toast toast-fixo"
    :class="{
      erro: store.toastErro,
      sucesso: store.toastSucesso,
    }"
    role="alert"
    aria-live="assertive"
  >
    <span v-if="store.toastErro" class="toast-icone" aria-hidden="true">!</span>
    <span v-else-if="store.toastSucesso" class="toast-icone" aria-hidden="true">✓</span>
    {{ store.toast }}
  </p>
</template>
