<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "aviso");
const ehConfirmacao = computed(() => store.aviso.tipo === "confirm");

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => (ehConfirmacao.value ? store.cancelarAviso() : store.fecharDialogs())
);
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-aviso"
    :class="{
      'dialog-aviso-nick': store.aviso.tipo === 'nick',
      'dialog-aviso-confirm': ehConfirmacao,
    }"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <div class="aviso-cabecalho">
      <span class="aviso-icone" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="28" height="28">
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </span>
      <div class="aviso-cabecalho-texto">
        <h2>{{ store.aviso.titulo }}</h2>
        <p class="dialog-sub aviso-mensagem">{{ store.aviso.mensagem }}</p>
      </div>
      <BtnFecharDialog />
    </div>
    <div class="dialog-scroll dialog-scroll-aviso">
      <p v-if="store.aviso.dica" class="aviso-dica">{{ store.aviso.dica }}</p>
      <div v-if="store.aviso.tipo === 'nick'" class="aviso-campo-nick">
        <label for="avisoInputNick">Seu apelido na sala</label>
        <input
          id="avisoInputNick"
          v-model="store.aviso.nickTemp"
          type="text"
          maxlength="24"
          placeholder="Ex.: TermoFan42"
          autocomplete="nickname"
          class="input-redondo"
        />
        <p class="aviso-campo-hint">O nick no topo da página também será atualizado.</p>
      </div>
      <div
        class="dialog-acoes aviso-acoes"
        :class="{ 'aviso-acoes-confirm': ehConfirmacao }"
      >
        <button
          v-if="ehConfirmacao"
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.cancelarAviso()"
        >
          {{ store.aviso.textoBotaoSec }}
        </button>
        <button
          type="button"
          class="btn-modo btn-largo"
          :class="{ 'btn-modo-destaque': ehConfirmacao }"
          @click="store.confirmarAviso()"
        >
          {{ store.aviso.textoBotao }}
        </button>
      </div>
    </div>
  </dialog>
</template>
