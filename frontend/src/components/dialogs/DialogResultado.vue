<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import GradeCompartilhar from "../ui/GradeCompartilhar.vue";
import ConfeteAnimado from "../ui/ConfeteAnimado.vue";

const store = useTermoStore();
const r = store.resultado;
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "resultado");
const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

const iconeResultado = computed(() => {
  if (r.venceu) return "🏆";
  if (r.ehDiaria) return "🌙";
  return "💭";
});

const classeDialogo = computed(() => ({
  "resultado-diaria": r.confeteIntenso || r.ehDiaria,
  "resultado-venceu": r.venceu,
  "resultado-perdeu": r.venceu === false,
}));
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-resultado dialog-resultado-v2"
    :class="classeDialogo"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <ConfeteAnimado v-if="r.confete" :intenso="r.confeteIntenso" />

    <div class="dialog-cabecalho resultado-cabecalho">
      <span class="resultado-icone" aria-hidden="true">{{ iconeResultado }}</span>
      <div class="dialog-cabecalho-texto">
        <p v-if="r.ehDiaria" class="resultado-kicker">Palavra do dia</p>
        <h2>{{ r.titulo }}</h2>
        <p class="dialog-sub resultado-subtitulo">{{ r.texto }}</p>
        <p v-if="r.pontos" class="resultado-pontos-chip">{{ r.pontos }}</p>
      </div>
      <BtnFecharDialog />
    </div>

    <div class="dialog-scroll dialog-scroll-resultado">
      <GradeCompartilhar
        v-if="r.mostrarGrade"
        :texto="r.gradeTexto"
        :venceu="r.venceu"
        :tentativas-usadas="r.tentativasUsadas"
        :max-tentativas="r.maxTentativas"
        :eh-diaria="r.ehDiaria"
        :data-formatada="r.dataFormatada"
      />

      <div class="dialog-acoes resultado-acoes">
        <button
          v-if="r.mostrarCompartilhar"
          type="button"
          class="btn-modo btn-largo btn-destaque"
          @click="store.compartilharResultado()"
        >
          Compartilhar
        </button>
        <button
          v-if="r.mostrarCopiar"
          type="button"
          class="btn-modo btn-largo"
          @click="store.copiarTexto(r.gradeTexto, 'Resultado copiado!')"
        >
          Copiar emojis
        </button>
        <button
          v-if="r.mostrarRevanche"
          type="button"
          class="btn-modo"
          @click="store.fecharDialogs(); store.wsEnviar('revanche')"
        >
          Revanche na sala
        </button>
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.jogarDeNovo()"
        >
          {{ r.ehDiaria ? "Voltar ao início" : "Continuar" }}
        </button>
      </div>
    </div>
  </dialog>
</template>
