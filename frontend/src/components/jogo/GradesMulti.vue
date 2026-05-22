<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import GradeTermo from "./GradeTermo.vue";
import { TAMANHO_PALAVRA } from "../../utils/constantes.js";

const store = useTermoStore();

const classeLayout = computed(() => {
  const q = store.gradesMulti.length;
  if (q >= 4) return "grades-multi--quarteto";
  if (q >= 2) return "grades-multi--dueto";
  return "";
});

const grades = computed(() =>
  store.gradesMulti.map((g, indice) => {
    const max = store.maxTentativas;
    const linhas = [];
    const temDica = Object.values(store.teclado || {}).includes("presente");
    for (let i = 0; i < max; i++) {
      if (g.tentativas[i]) {
        linhas.push({
          ...g.tentativas[i],
          revelada: true,
          atual: false,
          animar: !!g.tentativas[i].animar,
        });
      } else if (i === store.tentativa && !store.encerrada) {
        linhas.push({
          letras: [...store.letras],
          estados: [],
          revelada: false,
          atual: true,
          comDica: temDica,
          indiceCursor: store.indiceCursor,
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
  <div class="grades-multi" :class="classeLayout">
    <div
      v-for="g in grades"
      :key="g.indice"
      class="grade-multi-item"
    >
      <span class="grade-multi-label">Palavra {{ g.indice + 1 }}</span>
      <GradeTermo
        :linhas="g.linhas"
        compacta
        :shake-linha="store.linhaShake"
        :editavel="!store.encerrada"
        @selecionar-celula="(_, col) => store.selecionarCelula(col)"
      />
    </div>
  </div>
</template>
