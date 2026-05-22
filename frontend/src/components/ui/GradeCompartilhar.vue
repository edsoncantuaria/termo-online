<script setup>
import { computed } from "vue";
import { ParsearGradeCompartilhar } from "../../utils/jogo.js";

const props = defineProps({
  texto: { type: String, default: "" },
  venceu: { type: Boolean, default: null },
  tentativasUsadas: { type: Number, default: null },
  maxTentativas: { type: Number, default: 6 },
  ehDiaria: { type: Boolean, default: false },
  dataFormatada: { type: String, default: "" },
});

const parsed = computed(() => ParsearGradeCompartilhar(props.texto));

const meta = computed(() => {
  const P = parsed.value;
  const venceu =
    props.venceu !== null && props.venceu !== undefined
      ? props.venceu
      : P.venceu;
  const tent =
    props.tentativasUsadas ?? P.tentativasUsadas ?? null;
  const max = props.maxTentativas || P.maxTentativas || 6;
  const ehDiaria = props.ehDiaria || P.modo === "diaria";
  return {
    ehDiaria,
    venceu,
    tent,
    max,
    dataFormatada:
      props.dataFormatada || P.dataFormatada || "Hoje",
    grade: P.grade,
  };
});

const tituloCard = computed(() =>
  meta.value.ehDiaria ? "Resultado do jogo de hoje" : "Sua grade"
);

const seloClasse = computed(() => {
  if (meta.value.venceu === true) return "selo-venceu";
  if (meta.value.venceu === false) return "selo-perdeu";
  return "selo-neutro";
});

const seloTexto = computed(() => {
  if (meta.value.venceu === true) {
    const t = meta.value.tent;
    return t ? `Acertou em ${t}/${meta.value.max}` : "Vitória";
  }
  if (meta.value.venceu === false) return "Não acertou";
  return "Resultado";
});
</script>

<template>
  <div
    class="resultado-grade-card"
    :class="{ 'resultado-grade-card--diaria': meta.ehDiaria }"
  >
    <div class="resultado-grade-topo">
      <div>
        <p class="resultado-grade-kicker">
          {{ meta.ehDiaria ? "Palavra do dia" : "Termo Online" }}
        </p>
        <h3 class="resultado-grade-titulo">{{ tituloCard }}</h3>
        <p class="resultado-grade-data">{{ meta.dataFormatada }}</p>
      </div>
      <span class="resultado-grade-selo" :class="seloClasse">
        {{ seloTexto }}
      </span>
    </div>

    <div
      v-if="meta.grade.length"
      class="resultado-grade-grid"
      role="img"
      :aria-label="`Grade com ${meta.grade.length} tentativas`"
    >
      <div
        v-for="(linha, i) in meta.grade"
        :key="i"
        class="resultado-grade-linha"
      >
        <span
          v-for="(tile, j) in linha"
          :key="j"
          class="tile tile-resultado"
          :class="tile.tipo"
        />
      </div>
    </div>
    <p v-else class="resultado-grade-vazio">Grade indisponível.</p>

    <p class="resultado-grade-legenda" aria-hidden="true">
      <span class="legenda-item"><span class="tile tile-legenda correto" /> certa</span>
      <span class="legenda-item"><span class="tile tile-legenda presente" /> outro lugar</span>
      <span class="legenda-item"><span class="tile tile-legenda ausente" /> ausente</span>
    </p>
  </div>
</template>
