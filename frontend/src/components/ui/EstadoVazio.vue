<script setup>
defineProps({
  icone: { type: String, default: "—" },
  titulo: { type: String, default: "Nada por aqui" },
  texto: { type: String, default: "" },
});
</script>

<template>
  <li class="estado-vazio">
    <span class="estado-vazio-icone" aria-hidden="true">{{ icone }}</span>
    <span class="estado-vazio-texto">
      <strong>{{ titulo }}</strong>
      <span v-if="texto">{{ texto }}</span>
    </span>
  </li>
</template>
