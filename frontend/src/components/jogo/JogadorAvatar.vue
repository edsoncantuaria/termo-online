<script setup>
import { computed } from "vue";
import AvatarIlustracao from "../ui/AvatarIlustracao.vue";
import { AvatarPadraoDeNick, AvatarValido, MetaAvatar } from "../../utils/avatares.js";

const props = defineProps({
  nome: { type: String, required: true },
  avatarId: { type: String, default: "" },
  pequeno: { type: Boolean, default: false },
});

const idEfetivo = computed(() => {
  const bruto = (props.avatarId || "").trim();
  return AvatarValido(bruto) ? bruto : AvatarPadraoDeNick(props.nome);
});

const meta = computed(() => MetaAvatar(idEfetivo.value));
</script>

<template>
  <span
    class="jogador-avatar jogador-avatar--ilustrado"
    :class="{ 'jogador-avatar-sm': pequeno }"
    :style="{ '--avatar-cor': meta.corFundo }"
    :title="meta.nome"
    aria-hidden="true"
  >
    <AvatarIlustracao :avatar-id="idEfetivo" />
  </span>
</template>
