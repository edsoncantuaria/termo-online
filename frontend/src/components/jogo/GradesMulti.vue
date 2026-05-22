<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import GradeTermo from "./GradeTermo.vue";
import { TAMANHO_PALAVRA } from "../../utils/constantes.js";

const store = useTermoStore();

const grades = computed(() =>
  store.gradesMulti.map((g, indice) => {
    const max = store.maxTentativas;
    const linhas = [];
    for (let i = 0; i < max; i++) {
      if (g.tentativas[i]) {
        linhas.push({
          ...g.tentativas[i],
          revelada: true,
          atual: false,
          animar: !!g.tentativas[i].animar,
        });
      } else {
        linhas.push({
          letras: Array(TAMANHO_PALAVRA).fill(""),
          estados: [],
          revelada: false,
          atual: false,
        });
      }
    }
    return { indice, linhas };
  })
);
</script>

<template>
  <div class="grades-multi">
    <div
      v-for="g in grades"
      :key="g.indice"
      class="grade-multi-item"
    >
      <span class="grade-multi-label">#{{ g.indice + 1 }}</span>
      <GradeTermo :linhas="g.linhas" />
    </div>
  </div>
</template>
