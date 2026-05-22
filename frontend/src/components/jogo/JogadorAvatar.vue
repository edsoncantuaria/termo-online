<script setup>
import { InicialNick, CorAvatarNick } from "../../utils/jogador.js";

defineProps({
  nome: { type: String, required: true },
  pequeno: { type: Boolean, default: false },
});
</script>

<template>
  <span
    class="jogador-avatar"
    :class="{ 'jogador-avatar-sm': pequeno }"
    :style="{ '--avatar-cor': CorAvatarNick(nome) }"
    aria-hidden="true"
  >
    {{ InicialNick(nome) }}
  </span>
</template>
