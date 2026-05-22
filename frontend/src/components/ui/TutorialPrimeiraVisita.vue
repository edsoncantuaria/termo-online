<script setup>
import { ref } from "vue";

const emit = defineEmits(["fechar"]);

const passo = ref(0);

const passos = [
  {
    titulo: "Como jogar",
    texto: "Adivinhe a palavra de 5 letras em até 6 tentativas.",
    demo: ["correto", "", "", "", ""],
    letras: ["T", "", "", "", ""],
  },
  {
    titulo: "Verde — certo",
    texto: "A letra está na posição correta.",
    demo: ["correto", "ausente", "ausente", "ausente", "ausente"],
    letras: ["T", "E", "R", "M", "O"],
  },
  {
    titulo: "Dourado — existe",
    texto: "A letra está na palavra, mas em outro lugar.",
    demo: ["presente", "ausente", "ausente", "ausente", "ausente"],
    letras: ["E", "T", "R", "M", "O"],
  },
  {
    titulo: "Cinza — não está",
    texto: "Essa letra não faz parte da palavra.",
    demo: ["ausente", "ausente", "ausente", "ausente", "ausente"],
    letras: ["X", "Y", "Z", "W", "Q"],
  },
];

function avancar() {
  if (passo.value < passos.length - 1) passo.value++;
  else emit("fechar");
}

function pular() {
  emit("fechar");
}
</script>

<template>
  <div class="tutorial-overlay" role="dialog" aria-modal="true" aria-labelledby="tutorial-titulo">
    <div class="tutorial-card">
      <p class="tutorial-passo">Passo {{ passo + 1 }} de {{ passos.length }}</p>
      <h2 id="tutorial-titulo">{{ passos[passo].titulo }}</h2>
      <p>{{ passos[passo].texto }}</p>
      <div class="tutorial-demo">
        <span
          v-for="(est, i) in passos[passo].demo"
          :key="i"
          class="tile demo"
          :class="est || 'vazio'"
        >
          {{ passos[passo].letras[i] || "" }}
        </span>
      </div>
      <div class="tutorial-acoes">
        <button type="button" class="btn-modo btn-modo-sec" @click="pular">Pular</button>
        <button type="button" class="btn-modo" @click="avancar">
          {{ passo < passos.length - 1 ? "Próximo" : "Começar" }}
        </button>
      </div>
    </div>
  </div>
</template>
