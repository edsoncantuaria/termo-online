<script setup>
import JogadorAvatar from "../jogo/JogadorAvatar.vue";

const props = defineProps({
  jogador: { type: Object, required: true },
  criadorId: { type: String, default: null },
  souHost: { type: Boolean, default: false },
});

const emit = defineEmits(["expulsar"]);
</script>

<template>
  <li
    class="jogador-item"
    :class="{
      'jogador-eu': jogador.souEu,
      'jogador-host': jogador.idJogador === criadorId,
      'jogador-offline': jogador.conectado === false,
      'jogador-pronto': jogador.pronto,
    }"
  >
    <span class="jogador-avatar-wrap">
      <JogadorAvatar :nome="jogador.nomeJogador" />
      <span
        v-if="jogador.idJogador === criadorId"
        class="jogador-host-badge"
        title="Host"
      >★</span>
    </span>
    <span class="jogador-info">
      <span class="jogador-nome">{{ jogador.nomeJogador }}</span>
      <span class="jogador-meta">
        <span v-if="jogador.souEu" class="jogador-tag">você</span>
        <span
          v-if="jogador.espectador"
          class="jogador-tag"
        >espectador</span>
        <span
          v-else-if="jogador.conectado === false"
          class="jogador-tag jogador-tag-offline"
        >offline</span>
        <span
          v-else-if="jogador.pronto"
          class="jogador-tag jogador-tag-pronto"
        >pronto</span>
        <span v-else class="jogador-tag jogador-tag-aguardando">aguardando</span>
      </span>
    </span>
    <button
      v-if="souHost && !jogador.souEu && !jogador.espectador"
      type="button"
      class="jogador-kick"
      title="Remover da sala"
      aria-label="Remover jogador da sala"
      @click="emit('expulsar', jogador.idJogador)"
    >
      ×
    </button>
  </li>
</template>
