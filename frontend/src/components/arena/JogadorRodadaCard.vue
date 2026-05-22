<script setup>
import { computed } from "vue";
import JogadorAvatar from "../jogo/JogadorAvatar.vue";
import GradeTermo from "../jogo/GradeTermo.vue";
import { StatusJogadorRodada } from "../../utils/jogador.js";
import { NormalizarTentativa } from "../../utils/jogo.js";
import { TAMANHO_PALAVRA } from "../../utils/constantes.js";

const props = defineProps({
  jogador: { type: Object, required: true },
  verOutros: { type: Boolean, default: false },
  maxTentativas: { type: Number, default: 6 },
});

const status = computed(() =>
  StatusJogadorRodada(props.jogador, props.maxTentativas)
);

const linhasMini = computed(() => {
  if (!props.verOutros || props.jogador.espectador) return [];
  const tentativas = props.jogador.tentativas || [];
  return tentativas.map((t) => ({
    ...NormalizarTentativa(t),
    revelada: true,
    atual: false,
  }));
});

const pips = computed(() => {
  const usadas = props.jogador.tentativasUsadas || 0;
  return Array.from({ length: props.maxTentativas }, (_, i) => ({
    usada: i < usadas,
    acerto: props.jogador.venceu && i === usadas - 1,
  }));
});
</script>

<template>
  <article
    class="jogador-rodada-card"
    :class="[
      status.classe,
      { 'jogador-venceu': jogador.venceu },
      { 'jogador-finalizou': jogador.finalizou && !jogador.venceu },
      { 'jogador-espectador': jogador.espectador },
    ]"
    :data-jogador-id="jogador.idJogador"
  >
    <div class="jogador-rodada-topo">
      <JogadorAvatar :nome="jogador.nomeJogador" pequeno />
      <div class="jogador-rodada-ident">
        <span class="jogador-rodada-nome">{{ jogador.nomeJogador }}</span>
        <span class="jogador-rodada-status">{{ status.texto }}</span>
      </div>
    </div>
    <div class="jogador-rodada-corpo">
      <GradeTermo
        v-if="verOutros && !jogador.espectador && linhasMini.length"
        :linhas="linhasMini"
        compacta
      />
      <div
        v-else-if="!jogador.espectador"
        class="progresso-tentativas"
        :aria-label="`${jogador.tentativasUsadas || 0} de ${maxTentativas} tentativas`"
      >
        <span
          v-for="(pip, i) in pips"
          :key="i"
          class="tentativa-pip"
          :class="{ usada: pip.usada, acerto: pip.acerto }"
        />
      </div>
      <p v-else class="jogador-rodada-hint">Acompanha a partida sem jogar.</p>
    </div>
  </article>
</template>
