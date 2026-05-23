<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";

const store = useTermoStore();
const j = computed(() => store.jogoAtivo);

const ehOnline = computed(
  () => j.value?.tipo === "arena" || j.value?.tipo === "ranqueada"
);

const resultadoPendente = computed(() => !!j.value?.resultadoPendente);

const badgeClasse = computed(() => {
  if (!j.value) return "";
  if (ehOnline.value && j.value.pausada) return "hero-jogo-ativo-badge--pausa";
  if (j.value.emTempoDeJogo) return "hero-jogo-ativo-badge--jogo";
  return "hero-jogo-ativo-badge--aguardo";
});

const badgeTexto = computed(() => {
  if (!j.value) return "";
  if (ehOnline.value && j.value.pausada) return "Urgente";
  if (j.value.emTempoDeJogo) return "Em jogo";
  return "Aguardando";
});

const nivelUrgencia = computed(() => {
  if (!ehOnline.value || !j.value?.pausada) return 0;
  const Abandono = j.value.segundosAteAbandono;
  const Pausa = j.value.segundosPausaRestantes;
  if (Abandono != null && Abandono <= 30) return 2;
  if (Pausa != null && Pausa <= 20) return 2;
  if (Abandono != null && Abandono <= 60) return 1;
  return 1;
});

const classesHero = computed(() => ({
  "hero-jogo-ativo--pulso":
    ehOnline.value && j.value?.pausada && !resultadoPendente.value,
  "hero-jogo-ativo--critico":
    ehOnline.value && nivelUrgencia.value >= 2 && !resultadoPendente.value,
  "hero-jogo-ativo--alerta":
    ehOnline.value &&
    j.value?.pausada &&
    nivelUrgencia.value === 1 &&
    !resultadoPendente.value,
}));

const mostrarContagemPausa = computed(
  () =>
    ehOnline.value &&
    j.value?.pausada &&
    j.value.segundosPausaRestantes != null &&
    j.value.segundosPausaRestantes >= 0
);

const mostrarContagemAbandono = computed(
  () =>
    (j.value?.tipo === "ranqueada" || j.value?.tipo === "arena") &&
    j.value.segundosAteAbandono != null &&
    j.value.segundosAteAbandono >= 0
);

const ehRanqueada = computed(() => j.value?.tipo === "ranqueada");

const pontosAtuais = computed(
  () =>
    j.value?.pontosRanqueadaAtual ??
    store.conta?.pontosRanqueada ??
    0
);

const perdaRp = computed(() => {
  if (!ehRanqueada.value || j.value?.semPenalidade) return 0;
  if (j.value?.penalidadeAbandonoRp != null) return j.value.penalidadeAbandonoRp;
  return Math.min(12, Math.max(8, 10));
});

const pontosDepois = computed(() => {
  if (j.value?.pontosAposAbandonoEstimado != null) {
    return j.value.pontosAposAbandonoEstimado;
  }
  return Math.max(0, pontosAtuais.value - perdaRp.value);
});

const mostrarAlertaRp = computed(
  () => ehRanqueada.value && !j.value?.semPenalidade && perdaRp.value > 0
);

function formatarRelogio(Seg) {
  const N = Math.max(0, Math.floor(Number(Seg) || 0));
  const M = Math.floor(N / 60);
  const S = N % 60;
  if (M > 0) return `${M}:${String(S).padStart(2, "0")}`;
  return `${S}s`;
}
</script>

<template>
  <article
    v-if="j?.ativo"
    class="hero-jogo-ativo"
    :class="classesHero"
    role="region"
    aria-label="Partida em andamento"
    aria-live="polite"
  >
    <div class="hero-jogo-ativo-aura" aria-hidden="true" />

    <div class="hero-jogo-ativo-cabecalho">
      <span class="hero-jogo-ativo-badge" :class="badgeClasse">{{ badgeTexto }}</span>
      <h2 class="hero-jogo-ativo-titulo">{{ j.titulo }}</h2>
    </div>

    <p v-if="ehOnline && j.pausada" class="hero-jogo-ativo-chamada">
      Reconecte agora — o tempo está passando.
    </p>

    <p class="hero-jogo-ativo-estado">{{ j.textoEstado }}</p>

    <div v-if="mostrarAlertaRp" class="hero-alerta-rp">
      <p class="hero-alerta-rp-titulo">Se abandonar agora</p>
      <p class="hero-alerta-rp-valor">
        <span class="hero-alerta-rp-perda">−{{ perdaRp }} pontos</span>
      </p>
      <p class="hero-alerta-rp-transicao">
        <span>{{ pontosAtuais }}</span>
        <span class="hero-alerta-rp-seta" aria-hidden="true">→</span>
        <span class="hero-alerta-rp-depois">{{ pontosDepois }} RP</span>
      </p>
    </div>

    <div
      v-if="mostrarContagemPausa || mostrarContagemAbandono"
      class="hero-jogo-ativo-timers"
    >
      <div v-if="mostrarContagemPausa" class="hero-timer hero-timer--pausa">
        <span class="hero-timer-label">{{
          j.souJogadorPausado ? "Volte em" : "Retoma em"
        }}</span>
        <strong class="hero-timer-valor">{{
          formatarRelogio(j.segundosPausaRestantes)
        }}</strong>
      </div>
      <div
        v-if="mostrarContagemAbandono"
        class="hero-timer"
        :class="{
          'hero-timer--perigo': j.segundosAteAbandono <= 45,
        }"
      >
        <span class="hero-timer-label">{{
          j.souJogadorPausado ? "Derrota em" : "Abandono dele em"
        }}</span>
        <strong class="hero-timer-valor">{{
          formatarRelogio(j.segundosAteAbandono)
        }}</strong>
      </div>
    </div>

    <p v-if="j.codigoSala" class="hero-jogo-ativo-codigo">
      Sala <strong>{{ j.codigoSala }}</strong>
    </p>

    <div class="hero-jogo-ativo-acoes">
      <button
        type="button"
        class="btn-modo btn-modo-destaque btn-largo hero-btn-reconectar"
        :disabled="store.carregandoJogoAtivo"
        @click="store.reconectarJogoAtivo()"
      >
        {{
          store.carregandoJogoAtivo
            ? "Conectando…"
            : resultadoPendente
              ? j.voltarParaLobby
                ? "Voltar à sala"
                : "Ver resultado"
              : ehOnline
                ? "Reconectar agora"
                : "Continuar partida"
        }}
      </button>
      <button
        v-if="!resultadoPendente"
        type="button"
        class="btn-modo btn-modo-sec btn-largo hero-btn-abandonar"
        :disabled="store.carregandoJogoAtivo"
        @click="store.abandonarJogoAtivo()"
      >
        {{
          mostrarAlertaRp
            ? `Abandonar (−${perdaRp} RP)`
            : "Abandonar partida"
        }}
      </button>
    </div>

    <p class="hero-jogo-ativo-dica">
      <template v-if="ehOnline && j.pausada">
        Outros modos ficam bloqueados até reconectar ou abandonar.
      </template>
      <template v-else-if="j.tipo === 'solo' && store.contaRegistrada">
        Progresso salvo na conta.
      </template>
      <template v-else-if="j.tipo === 'solo'">
        Partida salva neste navegador.
      </template>
      <template v-else-if="ehOnline && store.contaRegistrada">
        Sua partida fica salva na conta — pode continuar em outro aparelho.
      </template>
      <template v-else-if="ehOnline">
        Partida salva neste navegador. Crie uma conta para sincronizar entre dispositivos.
      </template>
      <template v-else-if="store.contaRegistrada">
        Progresso salvo na conta.
      </template>
      <template v-else>
        Partida salva neste navegador.
      </template>
    </p>
  </article>
</template>
