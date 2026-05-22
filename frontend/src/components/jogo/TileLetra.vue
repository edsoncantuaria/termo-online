<script setup>
defineProps({
  letra: { type: String, default: "" },
  estado: { type: String, default: "" },
  revelada: { type: Boolean, default: false },
  atual: { type: Boolean, default: false },
  animar: { type: Boolean, default: false },
  cursor: { type: Boolean, default: false },
  clicavel: { type: Boolean, default: false },
});
</script>

<template>
  <div
    class="tile"
    :class="{
      preenchida: atual && letra,
      'tile-vazia': atual && !letra && !revelada,
      revelada,
      'tile-cursor': cursor && !revelada,
      'tile-clicavel': clicavel,
      [estado]: revelada && estado,
      'tile-animar': animar,
    }"
    :role="clicavel ? 'button' : undefined"
    :tabindex="clicavel ? 0 : undefined"
    @click="$emit('click')"
    @keydown.enter.prevent="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    {{ letra }}
  </div>
</template>
