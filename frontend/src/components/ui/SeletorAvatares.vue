<script setup>
import { ref, watch } from "vue";
import AvatarIlustracao from "./AvatarIlustracao.vue";
import { AVATARES } from "../../utils/avatares.js";

const props = defineProps({
  modelValue: { type: String, required: true },
  salvando: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "salvar"]);

const selecionado = ref(props.modelValue);

watch(
  () => props.modelValue,
  (v) => {
    selecionado.value = v;
  }
);

function escolher(id) {
  if (props.salvando) return;
  selecionado.value = id;
  emit("update:modelValue", id);
  emit("salvar", id);
}
</script>

<template>
  <div class="seletor-avatares" role="group" aria-label="Escolher avatar">
    <button
      v-for="a in AVATARES"
      :key="a.id"
      type="button"
      class="seletor-avatares-item"
      :class="{
        'seletor-avatares-item--ativo': selecionado === a.id,
        'seletor-avatares-item--salvando': salvando,
      }"
      :title="a.nome"
      :aria-label="`Avatar ${a.nome}`"
      :aria-pressed="selecionado === a.id"
      :disabled="salvando"
      @click="escolher(a.id)"
    >
      <AvatarIlustracao :avatar-id="a.id" />
      <span class="seletor-avatares-nome">{{ a.nome }}</span>
    </button>
  </div>
</template>
