<script setup>
import { onMounted, ref, watch } from "vue";
import QRCode from "qrcode";

const props = defineProps({
  texto: { type: String, required: true },
  tamanho: { type: Number, default: 160 },
  rotulo: { type: String, default: "" },
});

const dataUrl = ref("");

async function gerar() {
  if (!props.texto) {
    dataUrl.value = "";
    return;
  }
  try {
    dataUrl.value = await QRCode.toDataURL(props.texto, {
      width: props.tamanho,
      margin: 1,
      color: { dark: "#14111c", light: "#f4f2f7" },
    });
  } catch {
    dataUrl.value = "";
  }
}

onMounted(gerar);
watch(() => props.texto, gerar);
</script>

<template>
  <figure v-if="dataUrl" class="qr-bloco">
    <img :src="dataUrl" :width="tamanho" :height="tamanho" :alt="rotulo || 'QR code'" />
    <figcaption v-if="rotulo">{{ rotulo }}</figcaption>
  </figure>
</template>
