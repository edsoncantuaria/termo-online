<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const f = store.formCriarSala;
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "criarSala");
const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-criar-sala"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <div class="dialog-cabecalho">
      <div class="dialog-cabecalho-texto">
        <h2>Criar sala</h2>
        <p class="dialog-sub">Configure a partida e compartilhe o código com os amigos.</p>
      </div>
      <BtnFecharDialog />
    </div>
    <div class="dialog-scroll dialog-scroll-form">
    <form @submit.prevent="store.submeterCriarSala">
      <div class="form-grid">
        <label class="campo-slider">
          <span>Jogadores <strong>{{ f.maxJogadores }}</strong></span>
          <input v-model.number="f.maxJogadores" type="range" min="2" max="8" />
        </label>
        <label class="toggle">
          <input v-model="f.mesmaPalavra" type="checkbox" />
          <span class="toggle-ui" />
          <span>Mesma palavra</span>
        </label>
        <label class="toggle">
          <input v-model="f.verOutros" type="checkbox" />
          <span class="toggle-ui" />
          <span>Ver outros</span>
        </label>
        <label class="campo-select">
          <span>Modo da sessão</span>
          <select v-model="f.modoSessao" class="input-redondo select-redondo">
            <option value="pontos">Pontos infinitos — maratona</option>
            <option value="vitorias">Primeiro a N vitórias</option>
          </select>
        </label>
        <label v-show="f.modoSessao === 'vitorias'" class="campo-select">
          <span>Vitórias para ganhar</span>
          <select v-model.number="f.metaVitorias" class="input-redondo select-redondo">
            <option :value="3">3 vitórias</option>
            <option :value="5">5 vitórias</option>
            <option :value="7">7 vitórias</option>
            <option :value="10">10 vitórias</option>
          </select>
        </label>
        <label class="toggle">
          <input v-model="f.inicioAutoDois" type="checkbox" />
          <span class="toggle-ui" />
          <span>Iniciar com 2 jogadores</span>
        </label>
        <label class="campo-select">
          <span>Tempo por rodada</span>
          <select v-model.number="f.tempoLimite" class="input-redondo select-redondo">
            <option :value="0">Sem limite</option>
            <option :value="60">1 minuto</option>
            <option :value="120">2 minutos</option>
            <option :value="180">3 minutos</option>
            <option :value="300">5 minutos</option>
            <option :value="600">10 minutos</option>
          </select>
        </label>
        <input
          v-model="f.senha"
          type="text"
          maxlength="8"
          class="input-redondo"
          placeholder="Senha (opcional)"
        />
      </div>
      <div class="dialog-acoes">
        <button type="submit" class="btn-modo btn-largo">Confirmar sala</button>
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.fecharDialogs()"
        >
          Cancelar
        </button>
      </div>
    </form>
    </div>
  </dialog>
</template>
