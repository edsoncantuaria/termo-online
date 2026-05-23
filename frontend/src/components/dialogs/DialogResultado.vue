<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import GradeCompartilhar from "../ui/GradeCompartilhar.vue";
import ConfeteAnimado from "../ui/ConfeteAnimado.vue";
import EloPill from "../ui/EloPill.vue";

const store = useTermoStore();
const r = computed(() => store.resultado);
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "resultado");
const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

const iconeResultado = computed(() => {
  if (r.value.venceu) return "🏆";
  if (r.value.ehDiaria) return "🌙";
  return "💭";
});

const classeDialogo = computed(() => ({
  "resultado-diaria": r.value.confeteIntenso || r.value.ehDiaria,
  "resultado-venceu": r.value.venceu,
  "resultado-perdeu": r.value.venceu === false,
}));

const temConteudo = computed(
  () =>
    !!r.value.texto ||
    r.value.mostrarGrade ||
    !!r.value.pontos ||
    !!r.value.ranqueadaResumo
);

const deltaPositivo = computed(
  () => (r.value.ranqueadaResumo?.delta ?? 0) >= 0
);

const resumoRanq = computed(() => r.value.ranqueadaResumo);

const mostrarPromocaoElo = computed(
  () => !!resumoRanq.value?.subiuElo && resumoRanq.value?.nomeEloDepois
);

const mostrarDemocaoElo = computed(
  () => !!resumoRanq.value?.caiuElo && resumoRanq.value?.nomeEloAntes
);
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
        <h2>{{ r.titulo || "Resultado" }}</h2>
        <p v-if="r.texto" class="dialog-sub resultado-subtitulo">{{ r.texto }}</p>
        <p v-if="r.pontos" class="resultado-pontos-chip">{{ r.pontos }}</p>
      </div>
      <BtnFecharDialog />
    </div>

    <div class="dialog-scroll dialog-scroll-resultado">
      <section
        v-if="resumoRanq"
        class="resultado-ranqueada"
        aria-label="Resumo ranqueado"
      >
        <div
          v-if="mostrarPromocaoElo"
          class="resultado-elo-promocao"
          role="status"
        >
          <span class="resultado-elo-promocao-icone" aria-hidden="true">✦</span>
          <p class="resultado-elo-promocao-titulo">Você subiu de elo!</p>
          <div class="resultado-elo-promocao-pills">
            <EloPill
              v-if="resumoRanq.nomeEloAntes"
              :rotulo="resumoRanq.nomeEloAntes"
              :elo="resumoRanq.eloAntes"
              grande
            />
            <span class="resultado-elo-promocao-seta" aria-hidden="true">→</span>
            <EloPill
              :rotulo="resumoRanq.nomeEloDepois"
              :elo="resumoRanq.eloDepois"
              grande
            />
          </div>
        </div>

        <div
          v-else-if="mostrarDemocaoElo"
          class="resultado-elo-democao"
          role="status"
        >
          <span class="resultado-elo-democao-icone" aria-hidden="true">▼</span>
          <p class="resultado-elo-democao-titulo">Você caiu de elo</p>
          <div class="resultado-elo-promocao-pills">
            <EloPill
              :rotulo="resumoRanq.nomeEloAntes"
              :elo="resumoRanq.eloAntes"
              grande
            />
            <span class="resultado-elo-promocao-seta" aria-hidden="true">→</span>
            <EloPill
              :rotulo="resumoRanq.nomeEloDepois"
              :elo="resumoRanq.eloDepois"
              grande
            />
          </div>
        </div>

        <div
          v-else-if="resumoRanq.nomeEloDepois"
          class="resultado-elo-atual"
        >
          <span class="resultado-elo-atual-legenda">Seu elo</span>
          <EloPill
            :rotulo="resumoRanq.nomeEloDepois"
            :elo="resumoRanq.eloDepois"
            grande
          />
        </div>

        <p
          class="resultado-ranqueada-delta"
          :class="deltaPositivo ? 'resultado-ranqueada-delta--ganho' : 'resultado-ranqueada-delta--perda'"
        >
          {{ resumoRanq.delta >= 0 ? "+" : "" }}{{ resumoRanq.delta }} RP neste duelo
        </p>
        <p class="resultado-ranqueada-rp">
          <span>{{ resumoRanq.pontosAntes }}</span>
          <span aria-hidden="true">→</span>
          <span>{{ resumoRanq.pontosDepois }} RP</span>
        </p>
        <p v-if="resumoRanq.placarSerie" class="resultado-ranqueada-serie">
          Série {{ resumoRanq.placarSerie }}
        </p>
        <p class="resultado-ranqueada-record">
          {{ resumoRanq.vitorias }} vitórias · {{ resumoRanq.derrotas }} derrotas no ranqueado
        </p>
      </section>

      <GradeCompartilhar
        v-if="r.mostrarGrade"
        :texto="r.gradeTexto"
        :venceu="r.venceu"
        :tentativas-usadas="r.tentativasUsadas"
        :max-tentativas="r.maxTentativas"
        :eh-diaria="r.ehDiaria"
        :data-formatada="r.dataFormatada"
      />
      <p v-else-if="aberto && !temConteudo" class="resultado-grade-vazio">
        Não foi possível carregar o resumo da partida.
      </p>

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
          v-if="r.mostrarRevancheRanqueada"
          type="button"
          class="btn-modo btn-largo"
          @click="store.solicitarRevancheRanqueada()"
        >
          Revanche com {{ r.revancheOponenteNick || "oponente" }}
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
          {{
            r.ehArena
              ? "Voltar à sala"
              : r.ehDiaria || r.ehRanqueada
                ? "Voltar ao início"
                : "Continuar"
          }}
        </button>
      </div>
    </div>
  </dialog>
</template>
