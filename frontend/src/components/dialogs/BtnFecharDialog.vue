<script setup>
import { useTermoStore } from "../../stores/termo.js";

const props = defineProps({
  aoFechar: { type: Function, default: null },
});

const store = useTermoStore();

function fechar() {
  if (props.aoFechar) props.aoFechar();
  else store.fecharDialogs();
}
</script>

<template>
  <button
    type="button"
    class="btn-icone btn-fechar-dialog"
    aria-label="Fechar"
    @click="fechar"
  >
    ×
  </button>
</template>
