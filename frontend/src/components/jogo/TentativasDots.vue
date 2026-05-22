<script setup>
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
</script>

<template>
  <div class="tentativas-dots">
    <span
      v-for="(dot, i) in store.dotsTentativas"
      :key="i"
      class="dot"
      :class="{ usada: dot.usada, atual: dot.atual }"
    />
  </div>
</template>
