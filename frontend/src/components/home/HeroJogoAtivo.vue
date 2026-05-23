<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
const j = computed(() => store.jogoAtivo);

const badgeClasse = computed(() => {
  if (!j.value) return "";
  if (j.value.pausada) return "hero-jogo-ativo-badge--pausa";
  if (j.value.emTempoDeJogo) return "hero-jogo-ativo-badge--jogo";
  return "hero-jogo-ativo-badge--aguardo";
});

const badgeTexto = computed(() => {
  if (!j.value) return "";
  if (j.value.pausada) return "Pausada";
  if (j.value.emTempoDeJogo) return "Em jogo";
  return "Aguardando";
});
</script>

<template>
  <article
    v-if="j?.ativo"
    class="hero-jogo-ativo"
    role="region"
    aria-label="Partida em andamento"
  >
    <div class="hero-jogo-ativo-cabecalho">
      <span class="hero-jogo-ativo-badge" :class="badgeClasse">{{ badgeTexto }}</span>
      <h2 class="hero-jogo-ativo-titulo">{{ j.titulo }}</h2>
    </div>

    <p class="hero-jogo-ativo-estado">{{ j.textoEstado }}</p>

    <p v-if="j.codigoSala" class="hero-jogo-ativo-codigo">
      Sala <strong>{{ j.codigoSala }}</strong>
    </p>

    <div class="hero-jogo-ativo-acoes">
      <button
        type="button"
        class="btn-modo btn-modo-destaque btn-largo"
        :disabled="store.carregandoJogoAtivo"
        @click="store.reconectarJogoAtivo()"
      >
        {{ store.carregandoJogoAtivo ? "Conectando…" : "Reconectar" }}
      </button>
      <button
        type="button"
        class="btn-modo btn-modo-sec btn-largo"
        :disabled="store.carregandoJogoAtivo"
        @click="store.abandonarJogoAtivo()"
      >
        Abandonar partida
      </button>
    </div>

    <p class="hero-jogo-ativo-dica">
      <template v-if="store.contaRegistrada">
        Sua partida fica salva na conta — pode continuar em outro aparelho.
      </template>
      <template v-else>
        Partida salva neste navegador. Crie uma conta para sincronizar entre dispositivos.
      </template>
    </p>
  </article>
</template>
