<script setup>
import { computed } from "vue";
import { EstiloNivelCss } from "../../utils/progresso.js";
import AvatarIlustracao from "./AvatarIlustracao.vue";

const props = defineProps({
  avatarId: { type: String, default: "" },
  inicial: { type: String, default: "?" },
  corAvatar: { type: String, default: "#5fad62" },
  progresso: { type: Object, default: null },
  tamanho: { type: String, default: "medio" },
});

const usaIlustracao = computed(() => !!props.avatarId);

const estiloAnel = computed(() => EstiloNivelCss(props.progresso?.estiloNivel));
const nivel = computed(() => props.progresso?.nivel ?? 0);
const mostrarNivel = computed(
  () => props.progresso && !props.progresso.ehVisitante && nivel.value > 0
);
</script>

<template>
  <div
    class="perfil-anel"
    :class="[`perfil-anel--${tamanho}`, { 'perfil-anel--com-nivel': mostrarNivel }]"
    :style="estiloAnel"
  >
    <span
      class="perfil-anel-avatar"
      :class="{ 'perfil-anel-avatar--ilustrado': usaIlustracao }"
      :style="usaIlustracao ? undefined : { background: corAvatar }"
      aria-hidden="true"
    >
      <AvatarIlustracao v-if="usaIlustracao" :avatar-id="avatarId" />
      <template v-else>{{ inicial }}</template>
    </span>
    <span
      v-if="mostrarNivel"
      class="perfil-anel-nivel"
      :title="`Nível ${nivel}`"
      :aria-label="`Nível ${nivel}`"
    >{{ nivel }}</span>
  </div>
</template>
