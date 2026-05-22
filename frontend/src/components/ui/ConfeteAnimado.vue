<script setup>
import { onMounted, ref } from "vue";

const props = defineProps({
  intenso: { type: Boolean, default: false },
});

const CORES = ["#5fad62", "#c9b458", "#ff7b7b", "#9d96ad", "#f4f2f7"];
const pecas = ref([]);

onMounted(() => {
  const qtd = props.intenso ? 72 : 42;
  pecas.value = Array.from({ length: qtd }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    delay: `${Math.random() * 0.35}s`,
    dur: `${1.1 + Math.random() * 0.9}s`,
    cor: CORES[i % CORES.length],
    rot: `${Math.random() * 360}deg`,
    w: `${6 + Math.random() * 8}px`,
    h: `${10 + Math.random() * 14}px`,
  }));
});
</script>

<template>
  <div class="confete-cena" aria-hidden="true">
    <span
      v-for="p in pecas"
      :key="p.id"
      class="confete-peca"
      :style="{
        left: p.left,
        animationDelay: p.delay,
        animationDuration: p.dur,
        background: p.cor,
        width: p.w,
        height: p.h,
        '--rot': p.rot,
      }"
    />
  </div>
</template>
