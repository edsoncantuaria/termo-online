<script setup>
import { atualizacaoPwaDisponivel, aplicarAtualizacaoPwa } from "../../utils/pwa-atualizacao.js";

async function atualizar() {
  await aplicarAtualizacaoPwa();
}
</script>

<template>
  <div
    v-if="atualizacaoPwaDisponivel"
    class="banner-atualizacao-pwa"
    role="status"
    aria-live="polite"
  >
    <p class="banner-atualizacao-texto">
      Nova versão do Termo disponível.
    </p>
    <button type="button" class="btn-modo btn-modo-destaque banner-atualizacao-btn" @click="atualizar">
      Atualizar agora
    </button>
  </div>
</template>
