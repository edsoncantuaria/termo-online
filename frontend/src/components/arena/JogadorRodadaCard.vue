<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import JogadorAvatar from "../jogo/JogadorAvatar.vue";
import EloPill from "../ui/EloPill.vue";
import { RotuloRankDeJogador } from "../../utils/elos.js";
import GradeTermo from "../jogo/GradeTermo.vue";
import { StatusJogadorRodada } from "../../utils/jogador.js";
import {
  ContarVerdesTentativa,
  MelhorTentativaParaExibir,
  NormalizarTentativa,
} from "../../utils/jogo.js";

const store = useTermoStore();

const props = defineProps({
  jogador: { type: Object, required: true },
  verOutros: { type: Boolean, default: false },
  maxTentativas: { type: Number, default: 6 },
  /** Vários adversários na lateral — resumo compacto com expansão. */
  modoMultiplo: { type: Boolean, default: false },
  /** Ranqueado 1v1: só indica se o oponente já chutou. */
  modoCompetitivo: { type: Boolean, default: false },
});

const expandido = ref(false);

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

const melhorTentativa = computed(() =>
  MelhorTentativaParaExibir(props.jogador.tentativas)
);

const linhaResumo = computed(() => {
  const melhor = melhorTentativa.value;
  if (!melhor) return null;
  return { ...melhor, revelada: true, atual: false };
});

const verdesMelhor = computed(() =>
  melhorTentativa.value ? ContarVerdesTentativa(melhorTentativa.value) : 0
);

const usarResumo = computed(
  () =>
    props.modoMultiplo &&
    props.verOutros &&
    !props.jogador.espectador &&
    linhaResumo.value &&
    !expandido.value
);

const mostrarGradeCompleta = computed(
  () =>
    props.verOutros &&
    !props.jogador.espectador &&
    linhasMini.value.length &&
    (!props.modoMultiplo || expandido.value)
);

const avatarId = computed(() =>
  props.jogador.souEu ? store.avatarIdEfetivo() : props.jogador.avatarId
);

const pips = computed(() => {
  const usadas = props.jogador.tentativasUsadas || 0;
  return Array.from({ length: props.maxTentativas }, (_, i) => ({
    usada: i < usadas,
    acerto: props.jogador.venceu && i === usadas - 1,
  }));
});

function alternarExpansao() {
  expandido.value = !expandido.value;
}

watch(
  () => props.jogador.idJogador,
  () => {
    expandido.value = false;
  }
);

watch(
  () => props.jogador.tentativas?.length,
  () => {
    if (!props.modoMultiplo) expandido.value = false;
  }
);

const balaoFala = computed(() => {
  const b = store.balaoFala;
  if (!b || b.idJogador !== props.jogador.idJogador) return null;
  return b;
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
      { 'jogador-rodada-card--multi': modoMultiplo },
      { 'jogador-rodada-card--expandido': modoMultiplo && expandido },
    ]"
    :data-jogador-id="jogador.idJogador"
  >
    <Transition name="balao-fala">
      <div
        v-if="balaoFala"
        class="balao-fala balao-fala--card"
        :class="{ 'balao-fala--saindo': balaoFala.saindo }"
        role="status"
        aria-live="polite"
      >
        <p class="balao-fala-texto">{{ balaoFala.texto }}</p>
      </div>
    </Transition>
    <div class="jogador-rodada-topo">
      <JogadorAvatar
        :nome="jogador.nomeJogador"
        :avatar-id="avatarId"
        pequeno
      />
      <div class="jogador-rodada-ident">
        <span class="jogador-rodada-nome-linha">
          <span class="jogador-rodada-nome">{{ jogador.nomeJogador }}</span>
          <EloPill
            v-if="jogador.rotuloRank || jogador.eloNome"
            :rotulo="RotuloRankDeJogador(jogador)"
            :elo="jogador.elo"
            :elo-classe="jogador.eloClasse"
            :sem-rank="jogador.semRank"
          />
        </span>
        <span class="jogador-rodada-status">{{ status.texto }}</span>
      </div>
      <span
        v-if="usarResumo && verdesMelhor > 0"
        class="jogador-rodada-badge-verdes"
        :title="`${verdesMelhor} letra(s) verde(s) na melhor tentativa`"
      >
        {{ verdesMelhor }} verde{{ verdesMelhor === 1 ? "" : "s" }}
      </span>
    </div>

    <div v-if="usarResumo" class="jogador-rodada-resumo">
      <GradeTermo
        :linhas="[linhaResumo]"
        ultra-compacta
        :editavel="false"
      />
      <button
        type="button"
        class="btn-expandir-grade"
        :aria-expanded="false"
        @click="alternarExpansao"
      >
        {{ jogador.tentativas?.length || 0 }} tentativas
      </button>
    </div>

    <div v-else-if="modoCompetitivo && !jogador.espectador" class="jogador-rodada-corpo">
      <p class="jogador-rodada-hint jogador-rodada-hint--competitivo">
        {{ status.texto }}
      </p>
    </div>
    <div v-else class="jogador-rodada-corpo">
      <GradeTermo
        v-if="mostrarGradeCompleta"
        :linhas="linhasMini"
        compacta
        :editavel="false"
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
      <button
        v-if="modoMultiplo && verOutros && linhasMini.length && expandido"
        type="button"
        class="btn-expandir-grade btn-expandir-grade--fechar"
        :aria-expanded="true"
        @click="alternarExpansao"
      >
        Ocultar tentativas
      </button>
    </div>
  </article>
</template>
