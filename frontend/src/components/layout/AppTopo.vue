<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { InicialNick, CorAvatarNick, NickExibicao } from "../../utils/jogador.js";
import { AvatarEfetivo } from "../../utils/avatares.js";
import PerfilNivelAnel from "../ui/PerfilNivelAnel.vue";
import CloudiveMarcaTopo from "@cloudive-brand/components/CloudiveMarcaTopo.vue";
import { marcaCloudiveAtiva } from "../../utils/marca.js";
import { VERSAO_ROTULO } from "../../config/versao.js";
import EloPill from "../ui/EloPill.vue";

const store = useTermoStore();
const cloudive = marcaCloudiveAtiva();

const inicialAvatar = computed(() =>
  InicialNick(store.conta?.nick || store.nick)
);
const corAvatar = computed(() =>
  CorAvatarNick(store.conta?.nick || store.nick)
);
const avatarId = computed(() => AvatarEfetivo(store.conta, store.nick));
const mostrarCentro = computed(
  () => store.view !== "inicio" && store.tituloTopo !== "Termo"
);
</script>

<template>
  <header class="topo topo-v2" :class="{ 'topo-inicio': store.view === 'inicio' }">
    <button
      v-if="store.view !== 'inicio'"
      type="button"
      class="topo-btn topo-btn-voltar"
      aria-label="Voltar"
      @click="store.confirmarVoltarInicio()"
    >
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
        <path
          fill="none"
          stroke="currentColor"
          stroke-width="2.25"
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M15 6l-6 6 6 6"
        />
      </svg>
    </button>

    <button
      type="button"
      class="topo-brand"
      :class="{ 'topo-brand-click': store.view !== 'inicio' }"
      @click="store.view !== 'inicio' && store.confirmarVoltarInicio()"
    >
      <CloudiveMarcaTopo v-if="cloudive" />
      <template v-else>
        <span class="topo-logo-mark" aria-hidden="true">T</span>
        <span class="topo-logo-text">Termo</span>
      </template>
    </button>

    <div v-if="mostrarCentro" class="topo-centro">
      <span class="topo-pagina-titulo">{{ store.tituloTopo }}</span>
      <span class="topo-pagina-sub">{{ store.subtituloTopo }}</span>
    </div>

    <div class="topo-direita">
      <span class="topo-versao" aria-label="Versão do aplicativo">{{ VERSAO_ROTULO }}</span>
      <template v-if="store.conta">
        <button
          type="button"
          class="topo-usuario"
          :class="{ 'topo-usuario-visitante': store.conta.ehVisitante }"
          @click="store.abrirConta('entrada')"
        >
          <PerfilNivelAnel
            :avatar-id="avatarId"
            :inicial="inicialAvatar"
            :cor-avatar="corAvatar"
            :progresso="store.conta.progresso"
            tamanho="topo"
          />
          <span class="topo-usuario-texto">
            <span class="topo-usuario-nick">{{
              NickExibicao(store.conta.nick)
            }}</span>
            <span v-if="store.conta.ehVisitante" class="topo-usuario-meta">
              Conta temporária
            </span>
            <span v-else-if="store.conta.podeRanqueada" class="topo-usuario-meta topo-usuario-meta--rank">
              <template v-if="store.conta.progresso">
                Nv. {{ store.conta.progresso.nivel }} ·
              </template>
              <EloPill
                :rotulo="store.conta.rotuloRank || store.conta.eloNome"
                :elo="store.conta.elo"
                :elo-classe="store.conta.eloClasse"
                :sem-rank="store.conta.semRank"
              />
              <template v-if="!store.conta.semRank">
                · {{ store.conta.pontosRanqueada }} RP
              </template>
            </span>
          </span>
        </button>
        <button
          v-if="store.conta.ehVisitante"
          type="button"
          class="topo-btn topo-btn-cta"
          @click="store.abrirCriarConta()"
        >
          Criar conta
        </button>
      </template>
      <button
        v-if="!store.conta"
        type="button"
        class="topo-btn topo-btn-cta"
        @click="store.abrirConta('entrada')"
      >
        Entrar
      </button>

      <button
        v-if="store.conta && !store.conta.ehVisitante"
        type="button"
        class="topo-btn topo-btn-ghost"
        aria-label="Perfil, nível e badges"
        @click="store.abrirPerfil()"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            d="M4 19V5M10 19V9M16 19v-6M22 19V3"
          />
        </svg>
      </button>

      <button
        type="button"
        class="topo-btn topo-btn-ghost"
        aria-label="Ajuda e configurações"
        @click="store.abrirDialog('ajuda')"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 14v.01M12 8v4"
          />
        </svg>
      </button>
    </div>
  </header>
</template>
