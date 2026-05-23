<script setup>
import { computed } from "vue";
import { ClasseElo, EstiloInlineElo } from "../../utils/elos.js";

const props = defineProps({
  rotulo: { type: String, required: true },
  elo: { type: String, default: null },
  eloClasse: { type: String, default: null },
  semRank: { type: Boolean, default: false },
  grande: { type: Boolean, default: false },
});

const classe = computed(() => {
  if (props.semRank) return "elo-pill--sem-rank";
  return props.eloClasse || ClasseElo(props.elo);
});

const estilo = computed(() =>
  props.semRank ? null : EstiloInlineElo(props.elo)
);
</script>

<template>
  <span
    class="elo-pill"
    :class="[classe, { 'elo-pill--grande': grande }]"
    :style="estilo || undefined"
  >
    {{ rotulo }}
  </span>
</template>
