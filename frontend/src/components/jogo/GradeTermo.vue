<script setup>
import TileLetra from "./TileLetra.vue";

defineProps({
  linhas: { type: Array, required: true },
  compacta: { type: Boolean, default: false },
  shakeLinha: { type: Number, default: null },
  editavel: { type: Boolean, default: true },
});

const emit = defineEmits(["selecionar-celula"]);
</script>

<template>
  <div class="grade" :class="{ 'grade-mini': compacta, 'grade-mini-compacta': compacta }">
    <div
      v-for="(linha, idx) in linhas"
      :key="idx"
      class="linha"
      :class="{
        'linha-shake': shakeLinha === idx,
        'linha-com-dica': linha.comDica && linha.atual,
      }"
      :data-linha="idx"
    >
      <TileLetra
        v-for="(letra, col) in linha.letras"
        :key="col"
        :letra="letra"
        :estado="linha.estados?.[col]"
        :revelada="linha.revelada"
        :atual="linha.atual"
        :animar="linha.animar"
        :cursor="linha.atual && linha.indiceCursor === col"
        :clicavel="editavel && linha.atual && !linha.revelada"
        @click="emit('selecionar-celula', idx, col)"
      />
    </div>
  </div>
</template>
