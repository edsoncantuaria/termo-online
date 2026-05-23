<script setup>
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();

function rotulo(k) {
  if (k === "enter") return "ENTER";
  if (k === "back") return "⌫";
  return k.toUpperCase();
}

function aria(k) {
  if (k === "enter") return "Confirmar palavra";
  if (k === "back") return "Apagar letra";
  return `Letra ${k.toUpperCase()}`;
}
</script>

<template>
  <div class="teclado" :class="{ 'teclado-aguardando': store.carregandoChute }">
    <div
      v-for="(linha, idx) in store.tecladoLinhas"
      :key="idx"
      class="teclado-linha"
      :class="{
        'teclado-linha-meio': idx === 1,
        'teclado-linha-ultima': idx === 2,
        'teclado-linha-enter': idx === 3,
      }"
    >
      <button
        v-for="k in linha"
        :key="k"
        type="button"
        class="tecla"
        :class="[
          k === 'enter' || k === 'back' ? 'grande' : '',
          k === 'enter' ? 'tecla-enter' : '',
          k === 'back' ? 'tecla-back' : '',
          store.teclado[k],
        ]"
        :disabled="store.carregandoChute || store.encerrada"
        :aria-label="aria(k)"
        @click="store.onTecla(k)"
      >
        <span class="tecla-texto">{{ rotulo(k) }}</span>
      </button>
    </div>
  </div>
</template>
