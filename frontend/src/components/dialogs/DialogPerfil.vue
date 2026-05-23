<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { api } from "../../services/api.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import EstadoVazio from "../ui/EstadoVazio.vue";
import PerfilNivelAnel from "../ui/PerfilNivelAnel.vue";
import { InicialNick, CorAvatarNick } from "../../utils/jogador.js";
import { BarrasHistorico7d } from "../../utils/progresso.js";
import SeletorAvatares from "../ui/SeletorAvatares.vue";
import EloPill from "../ui/EloPill.vue";
import { NOMES_ELO, ORDEM_ELOS } from "../../utils/elos.js";

const store = useTermoStore();
const dialogo = ref(null);
const dialogoRankingInfo = ref(null);
const dialogoPartidas = ref(null);
const aberto = computed(() => store.dialogAberto === "perfil");
const salvandoAvatar = ref(false);
const carregandoPartidas = ref(false);
const ultimasPartidas = ref([]);
const LIMITE_PARTIDAS = 20;

const totalRanqueadosFmt = computed(() =>
  (store.totalRanqueados ?? 0).toLocaleString("pt-BR")
);
const progresso = computed(() => store.conta?.progresso);
const inicialAvatar = computed(() => InicialNick(store.conta?.nick));
const corAvatar = computed(() => CorAvatarNick(store.conta?.nick));
const avatarId = computed(() => store.avatarIdEfetivo());
const badgesDesbloqueadas = computed(() =>
  (progresso.value?.badges || []).filter((b) => b.desbloqueada)
);
const barrasHistorico = computed(() =>
  BarrasHistorico7d(progresso.value?.historico7d)
);
const metasConcluidas = computed(
  () => (progresso.value?.metasSemanais || []).filter((m) => m.concluida).length
);
const metasTotal = computed(() => progresso.value?.metasSemanais?.length ?? 0);
const eloExibicao = computed(
  () => store.conta?.rotuloRank || store.conta?.eloNome || "—"
);
const pontosRp = computed(() => store.conta?.pontosRanqueada ?? 0);
const partidasPorModo = computed(
  () => store.statsServidor?.partidasPorModo || []
);
const totalPartidasModos = computed(
  () =>
    store.statsServidor?.totalPartidasSolo ??
    partidasPorModo.value.reduce((s, m) => s + (m.partidas || 0), 0)
);
const nickBusca = ref("");

const ehMeuPerfil = computed(() => store.perfilVisualizacao === "eu");
const perfilOutro = computed(() => store.perfilOutro);

const contaExibida = computed(() =>
  ehMeuPerfil.value ? store.conta : perfilOutro.value?.perfil
);
const statsExibido = computed(() => {
  if (ehMeuPerfil.value) return store.statsServidor;
  if (ehPerfilVisitante.value) return null;
  return perfilOutro.value?.estatisticas;
});
const partidasPorModoExibido = computed(
  () => statsExibido.value?.partidasPorModo || []
);
const modosComPartida = computed(() =>
  partidasPorModoExibido.value.filter((m) => m.partidas > 0)
);
const totalPartidasModosExibido = computed(() =>
  ehMeuPerfil.value
    ? totalPartidasModos.value
    : partidasPorModoExibido.value
        .filter((m) => m.modo !== "ranqueada" && m.modo !== "treino_ranqueado")
        .reduce((s, m) => s + (m.partidas || 0), 0)
);

const nickExibido = computed(() =>
  ehMeuPerfil.value ? store.nick : perfilOutro.value?.nick || ""
);
const inicialExibido = computed(() => InicialNick(nickExibido.value));
const corExibida = computed(() => CorAvatarNick(nickExibido.value));
const avatarIdExibido = computed(() => {
  if (ehMeuPerfil.value) return avatarId.value;
  const id = contaExibida.value?.avatarId;
  return id || "";
});

const eloExibidoOutro = computed(
  () =>
    contaExibida.value?.rotuloRank ||
    contaExibida.value?.eloNome ||
    "—"
);
const pontosRpExibido = computed(
  () => contaExibida.value?.pontosRanqueada ?? 0
);
const posicaoExibida = computed(() =>
  ehMeuPerfil.value
    ? store.minhaPosicaoRanqueada
    : perfilOutro.value?.posicaoRanqueada
);
const rotuloPosicaoRank = computed(() => {
  const p = posicaoExibida.value;
  if (p == null || p < 1) return null;
  return `#${Number(p).toLocaleString("pt-BR")}`;
});
const totalRanqExibido = computed(() =>
  ehMeuPerfil.value
    ? store.totalRanqueados
    : perfilOutro.value?.totalRanqueados
);
const totalRanqFmtExibido = computed(() =>
  (totalRanqExibido.value ?? 0).toLocaleString("pt-BR")
);
const ehPerfilVisitante = computed(
  () => !ehMeuPerfil.value && perfilOutro.value?.tipo === "visitante"
);
const ehPerfilRegistradoOutro = computed(
  () => !ehMeuPerfil.value && perfilOutro.value?.tipo === "registrado"
);

const progressoExibido = computed(() => {
  if (ehMeuPerfil.value) return progresso.value;
  const c = contaExibida.value;
  if (!c || perfilOutro.value?.tipo !== "registrado" || c.nivel == null) return null;
  return {
    nivel: c.nivel,
    estiloNivel: { faixaNome: c.faixaNome },
    xpTotal: c.xpTotal,
    progressoPct: 0,
    xpNoNivel: 0,
    xpProximoNivel: 0,
  };
});

const carregandoConteudo = computed(() =>
  ehMeuPerfil.value ? store.carregandoPerfil : store.carregandoPerfilOutro
);

function totalVitoriasStats(st) {
  if (!st?.partidasPorModo?.length) return st?.vitoriasRanking ?? 0;
  return st.partidasPorModo.reduce((s, m) => s + (m.vitorias || 0), 0);
}

const resumoVitorias = computed(() => {
  if (ehMeuPerfil.value) return store.statVitorias;
  return totalVitoriasStats(statsExibido.value);
});

const resumoTaxa = computed(() => {
  const st = statsExibido.value;
  if (!st) return "—";
  return `${st.taxaVitoria ?? 0}%`;
});

const resumoExtra = computed(() => {
  const st = statsExibido.value;
  if (!st) return "";
  if (!ehMeuPerfil.value) {
    const pr = st.partidasPorModo?.find((m) => m.modo === "ranqueada");
    return `${pr?.partidas ?? 0} duelos ranqueados · ${pr?.vitorias ?? 0} vitórias ranqueadas`;
  }
  return store.statsExtraTexto;
});

const podeVerPartidas = computed(() => {
  if (ehMeuPerfil.value) return store.contaRegistrada;
  const o = perfilOutro.value;
  if (!o) return false;
  if (o.tipo === "registrado") return true;
  return (o.ultimasPartidas?.length ?? 0) > 0;
});

function buscarJogador() {
  store.buscarPerfilJogador(nickBusca.value);
}

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

function abrirRankingInfo() {
  dialogoRankingInfo.value?.showModal();
}

function fecharRankingInfo() {
  dialogoRankingInfo.value?.close();
}

function onCliqueForaRankingInfo(ev) {
  if (ev.target === dialogoRankingInfo.value) fecharRankingInfo();
}

function formatarDataPartida(dataHora) {
  if (!dataHora) return "—";
  const bruto = String(dataHora).trim();
  const d = new Date(bruto.includes("T") ? bruto : bruto.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return bruto;
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function subtituloPartida(p) {
  if (p.tipo === "ranqueada" && p.oponente) {
    return `vs ${p.oponente}`;
  }
  if (p.tentativas != null) {
    return `${p.tentativas} ${p.tentativas === 1 ? "tentativa" : "tentativas"}`;
  }
  return "";
}

async function carregarUltimasPartidas() {
  carregandoPartidas.value = true;
  try {
    const D = await api.contaUltimasPartidas();
    ultimasPartidas.value = (D.partidas || []).slice(0, LIMITE_PARTIDAS);
  } catch {
    ultimasPartidas.value = [];
    store.mostrarToast("Não foi possível carregar suas partidas.", true);
  } finally {
    carregandoPartidas.value = false;
  }
}

async function abrirPartidas() {
  if (!podeVerPartidas.value) {
    store.mostrarToast(
      perfilOutro.value?.mensagem ||
        "Só contas registradas têm histórico completo de partidas.",
      true
    );
    return;
  }
  dialogoPartidas.value?.showModal();
  if (ehMeuPerfil.value) {
    await carregarUltimasPartidas();
  } else {
    ultimasPartidas.value = perfilOutro.value?.ultimasPartidas || [];
  }
}

function fecharPartidas() {
  dialogoPartidas.value?.close();
}

function onCliqueForaPartidas(ev) {
  if (ev.target === dialogoPartidas.value) fecharPartidas();
}

watch(aberto, (v) => {
  if (!v) {
    fecharRankingInfo();
    fecharPartidas();
    store.voltarMeuPerfil();
    nickBusca.value = "";
  }
});

function classeRankingLinha(posicao) {
  if (posicao === 1) return "ranking-linha--ouro";
  if (posicao === 2) return "ranking-linha--prata";
  if (posicao === 3) return "ranking-linha--bronze";
  return "";
}

async function onSalvarAvatar(id) {
  salvandoAvatar.value = true;
  try {
    await store.salvarAvatar(id);
    store.fecharDialogAvatar();
  } finally {
    salvandoAvatar.value = false;
  }
}
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-perfil dialog-perfil-v2"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <header class="perfil-hero">
      <div class="perfil-hero-linha">
        <button
          v-if="ehMeuPerfil && store.conta"
          type="button"
          class="perfil-avatar-editar"
          aria-label="Alterar avatar"
          title="Alterar avatar"
          @click.stop="store.abrirDialogAvatar()"
        >
          <PerfilNivelAnel
            :avatar-id="avatarIdExibido"
            :inicial="inicialExibido"
            :cor-avatar="corExibida"
            :progresso="progressoExibido"
            tamanho="grande"
          />
          <span class="perfil-avatar-editar-icone" aria-hidden="true">✎</span>
        </button>
        <div v-else class="perfil-avatar-so-leitura" aria-hidden="true">
          <PerfilNivelAnel
            :avatar-id="avatarIdExibido"
            :inicial="inicialExibido"
            :cor-avatar="corExibida"
            :progresso="progressoExibido"
            tamanho="grande"
          />
        </div>

        <div class="perfil-hero-texto">
          <p class="perfil-kicker">
            {{ ehMeuPerfil ? "Seu perfil" : "Perfil de jogador" }}
          </p>
          <h2 class="perfil-hero-nick">{{ nickExibido }}</h2>
          <p
            v-if="!ehMeuPerfil && perfilOutro?.mensagem"
            class="perfil-aviso-visitante"
            role="status"
          >
            {{ perfilOutro.mensagem }}
          </p>
          <div
            v-if="ehMeuPerfil ? store.conta?.podeRanqueada : ehPerfilRegistradoOutro"
            class="perfil-hero-chips"
          >
            <EloPill
              :rotulo="ehMeuPerfil ? eloExibicao : eloExibidoOutro"
              :elo="contaExibida?.elo"
              :elo-classe="contaExibida?.eloClasse"
              :sem-rank="contaExibida?.semRank"
            />
            <span class="perfil-chip perfil-chip--rp">{{ pontosRpExibido }} RP</span>
            <span
              v-if="rotuloPosicaoRank"
              class="perfil-chip perfil-chip--pos"
              :title="
                ehMeuPerfil && totalRanqExibido
                  ? `Entre ${totalRanqFmtExibido} no ranking`
                  : 'Posição no ranking ranqueado'
              "
            >
              {{ rotuloPosicaoRank }}
            </span>
            <span
              v-else-if="ehMeuPerfil && store.conta?.podeRanqueada && totalRanqExibido"
              class="perfil-chip perfil-chip--muted"
            >
              {{ totalRanqFmtExibido }} jogadores
            </span>
          </div>
          <p v-if="progressoExibido?.nivel" class="perfil-hero-meta">
            Nv. <strong>{{ progressoExibido.nivel }}</strong>
            · {{ progressoExibido.estiloNivel.faixaNome }}
            <template v-if="progressoExibido.xpTotal != null">
              · {{ progressoExibido.xpTotal.toLocaleString("pt-BR") }} XP
            </template>
          </p>
        </div>

        <BtnFecharDialog />
      </div>

      <div
        v-if="ehMeuPerfil && progresso"
        class="perfil-hero-xp"
        role="progressbar"
        :aria-valuenow="progresso.progressoPct"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Progresso para o nível ${progresso.nivel + 1}`"
      >
        <div class="perfil-hero-xp-track">
          <div
            class="perfil-hero-xp-fill"
            :style="{ width: `${progresso.progressoPct}%` }"
          />
        </div>
        <span class="perfil-hero-xp-label">
          {{ progresso.xpNoNivel }} / {{ progresso.xpProximoNivel }} XP → nv.
          {{ progresso.nivel + 1 }}
        </span>
      </div>
    </header>

    <div class="dialog-scroll dialog-scroll-perfil">
      <section class="perfil-bloco perfil-bloco--busca" aria-label="Buscar jogador">
        <h3>Buscar jogador</h3>
        <form class="perfil-busca-form" @submit.prevent="buscarJogador">
          <input
            v-model="nickBusca"
            type="text"
            class="input-redondo perfil-busca-input"
            placeholder="Nick (ex.: maria)"
            maxlength="20"
            autocapitalize="none"
            autocomplete="off"
            :disabled="store.carregandoPerfilOutro"
          />
          <button
            type="submit"
            class="btn-modo btn-modo-destaque"
            :disabled="store.carregandoPerfilOutro || !nickBusca.trim()"
          >
            {{ store.carregandoPerfilOutro ? "Buscando…" : "Ver perfil" }}
          </button>
        </form>
        <button
          v-if="!ehMeuPerfil"
          type="button"
          class="btn-link-home perfil-voltar-meu"
          @click="store.voltarMeuPerfil()"
        >
          ← Voltar ao meu perfil
        </button>
      </section>

      <section
        v-if="ehMeuPerfil && store.conta?.podeRanqueada"
        class="perfil-bloco"
        aria-labelledby="perfil-ranking-titulo"
      >
        <div class="perfil-bloco-topo">
          <h3 id="perfil-ranking-titulo">Ranking ranqueado</h3>
          <div class="perfil-bloco-acoes">
            <span v-if="store.totalRanqueados" class="perfil-chip perfil-chip--muted">
              {{ totalRanqueadosFmt }} jogadores
            </span>
            <button
              type="button"
              class="btn-perfil-info"
              aria-label="Como funcionam os elos"
              title="Elos e ranking"
              @click="abrirRankingInfo"
            >
              ?
            </button>
          </div>
        </div>

        <ol
          v-if="carregandoConteudo"
          class="perfil-ranking-lista lista-loading"
          aria-busy="true"
        >
          <li v-for="n in 5" :key="n" class="skeleton-linha" />
        </ol>
        <ol v-else class="perfil-ranking-lista">
          <EstadoVazio
            v-if="!store.rankingRanqueado.length"
            icone="⚔️"
            titulo="Ninguém ranqueou ainda"
          />
          <template
            v-for="item in store.rankingRanqueado"
            :key="item.tipo === 'ellipsis' ? 'gap' : `${item.nick}-${item.posicao}`"
          >
            <li v-if="item.tipo === 'ellipsis'" class="ranking-ellipsis">···</li>
            <li
              v-else
              class="ranking-linha"
              :class="[
                classeRankingLinha(item.posicao),
                { 'ranking-linha--eu': item.souEu },
              ]"
            >
              <span class="ranking-linha-pos">{{ item.posicao }}</span>
              <div class="ranking-linha-corpo">
                <span class="ranking-linha-nick">{{ item.nick }}</span>
                <span class="ranking-linha-meta">
                  {{ item.eloNome }} · {{ item.pontos }} RP
                </span>
              </div>
            </li>
          </template>
        </ol>
      </section>

      <section
        v-else-if="ehMeuPerfil"
        class="perfil-bloco perfil-bloco--aviso"
      >
        <p class="perfil-bloco-texto">
          Crie uma conta para ranquear, ver o ranking global e duelar online.
        </p>
        <button type="button" class="btn-modo btn-largo" @click="store.abrirCriarConta()">
          Criar conta
        </button>
      </section>

      <section
        v-if="!ehPerfilVisitante"
        class="perfil-bloco"
        aria-labelledby="perfil-resumo-titulo"
      >
        <h3 id="perfil-resumo-titulo">Resumo</h3>
        <div v-if="carregandoConteudo" class="lista-loading" aria-busy="true">
          <div class="skeleton-linha" />
        </div>
        <template v-else>
          <div class="perfil-stats-mini">
            <div class="perfil-stat">
              <span class="perfil-stat-valor">{{ resumoVitorias }}</span>
              <span class="perfil-stat-label">Vitórias</span>
            </div>
            <div class="perfil-stat">
              <span class="perfil-stat-valor">{{
                ehMeuPerfil ? store.statSequencia : "—"
              }}</span>
              <span class="perfil-stat-label">Sequência</span>
            </div>
            <div class="perfil-stat">
              <span class="perfil-stat-valor">{{
                ehMeuPerfil ? store.statDiaria : statsExibido?.diariasVencidas ?? 0
              }}</span>
              <span class="perfil-stat-label">{{
                ehMeuPerfil ? "Diária hoje" : "Diárias (14d)"
              }}</span>
            </div>
            <div class="perfil-stat">
              <span class="perfil-stat-valor">{{ resumoTaxa }}</span>
              <span class="perfil-stat-label">Taxa vitória</span>
            </div>
          </div>
          <p v-if="resumoExtra" class="perfil-bloco-nota">{{ resumoExtra }}</p>
          <button
            type="button"
            class="btn-modo btn-modo-sec btn-largo perfil-btn-partidas"
            :disabled="!podeVerPartidas && ehMeuPerfil"
            @click="abrirPartidas"
          >
            Últimas {{ LIMITE_PARTIDAS }} partidas
          </button>
          <p
            v-if="!podeVerPartidas && ehMeuPerfil"
            class="perfil-bloco-nota perfil-bloco-nota--inline"
          >
            Histórico completo exige conta com e-mail.
          </p>
        </template>
      </section>

      <section
        v-if="!ehPerfilVisitante"
        class="perfil-bloco"
        aria-labelledby="perfil-modos-titulo"
      >
        <div class="perfil-bloco-topo">
          <h3 id="perfil-modos-titulo">Partidas por modo</h3>
          <span
            v-if="totalPartidasModosExibido > 0"
            class="perfil-chip perfil-chip--muted"
          >
            {{ totalPartidasModosExibido.toLocaleString("pt-BR") }} solo
          </span>
        </div>
        <ul
          v-if="carregandoConteudo"
          class="perfil-modos-grid lista-loading"
          aria-busy="true"
        >
          <li v-for="n in 4" :key="n" class="skeleton-linha" />
        </ul>
        <ul v-else-if="modosComPartida.length" class="perfil-modos-grid">
          <li
            v-for="m in modosComPartida"
            :key="m.modo"
            class="perfil-modo-card"
            :class="{ 'perfil-modo-card--treino': m.modo === 'treino_ranqueado' }"
          >
            <span class="perfil-modo-card-nome">{{ m.nome }}</span>
            <span class="perfil-modo-card-stats">
              <strong>{{ m.partidas }}</strong>
              <span v-if="m.vitorias > 0" class="perfil-modo-card-v">
                {{ m.vitorias }}V
              </span>
            </span>
          </li>
        </ul>
        <p v-else class="perfil-bloco-vazio">Nenhuma partida encerrada ainda.</p>
        <details
          v-if="partidasPorModoExibido.some((m) => !m.partidas)"
          class="perfil-modos-todos"
        >
          <summary>Ver todos os modos</summary>
          <ul class="perfil-modos-lista-compacta">
            <li
              v-for="m in partidasPorModoExibido"
              :key="m.modo"
              :class="{ 'perfil-modo-linha--vazio': !m.partidas }"
            >
              <span>{{ m.nome }}</span>
              <span>{{ m.partidas }} · {{ m.vitorias }}V</span>
            </li>
          </ul>
        </details>
      </section>

      <details
        v-if="ehMeuPerfil && progresso"
        class="perfil-bloco perfil-bloco--collapsible"
      >
        <summary class="perfil-bloco-summary">
          Progresso e metas
          <span class="perfil-chip perfil-chip--muted">
            {{ metasConcluidas }}/{{ metasTotal }} metas
          </span>
        </summary>
        <div class="perfil-bloco-corpo">
          <p v-if="progresso.xpCapDiario" class="perfil-xp-meta">
            Hoje: {{ progresso.xpGanhoHoje }} / {{ progresso.xpCapDiario }} XP
            · Eficiência {{ progresso.multiplicadorXpPct }}%
          </p>
          <p v-if="progresso.lembreteMetas" class="perfil-lembrete-metas" role="status">
            {{ progresso.lembreteMetas }}
          </p>

          <details v-if="barrasHistorico.length" class="perfil-colapsavel">
            <summary class="perfil-colapsavel-resumo">Últimos 7 dias</summary>
            <div class="perfil-colapsavel-corpo perfil-historico">
              <div class="perfil-historico-barras" aria-hidden="true">
                <div
                  v-for="b in barrasHistorico"
                  :key="b.dia"
                  class="perfil-historico-col"
                  :title="`${b.dia}: ${b.xp} XP, ${b.deltaRp >= 0 ? '+' : ''}${b.deltaRp} RP`"
                >
                  <div class="perfil-hist-xp" :style="{ height: `${b.alturaXp}%` }" />
                  <div
                    class="perfil-hist-rp"
                    :class="{ 'perfil-hist-rp--neg': b.deltaRp < 0 }"
                    :style="{ height: `${b.alturaRp}%` }"
                  />
                  <span class="perfil-hist-label">{{ b.dia }}</span>
                </div>
              </div>
              <p class="perfil-hist-legenda">
                <span class="perfil-hist-leg-xp">XP</span>
                <span class="perfil-hist-leg-rp">RP</span>
              </p>
            </div>
          </details>

          <details v-if="progresso.metasSemanais?.length" class="perfil-colapsavel">
            <summary class="perfil-colapsavel-resumo">
              Metas da semana ({{ metasConcluidas }}/{{ metasTotal }})
            </summary>
            <ul class="perfil-colapsavel-corpo perfil-metas-lista">
              <li v-for="m in progresso.metasSemanais" :key="m.id">
                <div class="perfil-meta-topo">
                  <strong>{{ m.nome }}</strong>
                  <span>{{ m.progresso }}/{{ m.meta }}</span>
                </div>
                <p class="perfil-meta-desc">{{ m.descricao }}</p>
                <div class="perfil-meta-barra">
                  <div
                    class="perfil-meta-fill"
                    :style="{
                      width: `${Math.min(100, (100 * m.progresso) / m.meta)}%`,
                    }"
                  />
                </div>
                <span v-if="m.recompensada" class="perfil-meta-ok">Recompensada</span>
                <span v-else-if="m.concluida" class="perfil-meta-ok">
                  +{{ m.xpRecompensa }} XP
                </span>
              </li>
            </ul>
          </details>

          <details class="perfil-colapsavel">
            <summary class="perfil-colapsavel-resumo">
              Badges ({{ badgesDesbloqueadas.length }}/{{ progresso.badgesTotal }})
            </summary>
            <ul class="perfil-colapsavel-corpo perfil-badges">
              <li
                v-for="b in progresso.badges"
                :key="b.id"
                :class="{
                  'perfil-badge--ok': b.desbloqueada,
                  'perfil-badge--bloq': !b.desbloqueada,
                }"
              >
                <span class="perfil-badge-icone" aria-hidden="true">{{ b.icone }}</span>
                <span>
                  <strong>{{ b.nome }}</strong>
                  <span class="perfil-badge-desc">{{ b.descricao }}</span>
                </span>
              </li>
            </ul>
          </details>
        </div>
      </details>

      <section
        v-if="ehMeuPerfil"
        class="perfil-bloco perfil-bloco--diaria"
        aria-labelledby="perfil-diaria-titulo"
      >
        <h3 id="perfil-diaria-titulo">Palavra do dia</h3>
        <ul
          v-if="store.carregandoPerfil"
          class="perfil-diaria-lista lista-loading"
          aria-busy="true"
        >
          <li v-for="n in 3" :key="n" class="skeleton-linha" />
        </ul>
        <ul v-else class="perfil-diaria-lista">
          <EstadoVazio
            v-if="!store.historicoDiaria.length"
            icone="📅"
            titulo="Nenhuma diária salva"
          />
          <li
            v-for="item in store.historicoDiaria"
            :key="item.dataDia"
            class="perfil-diaria-item"
          >
            <span class="perfil-diaria-data">{{
              new Date(item.dataDia + "T12:00:00").toLocaleDateString("pt-BR", {
                day: "numeric",
                month: "short",
              })
            }}</span>
            <span
              class="perfil-diaria-resultado"
              :class="item.venceu ? 'perfil-diaria-resultado--ok' : ''"
            >
              {{ item.venceu ? "Venceu" : "—" }}
              · {{ item.tentativasUsadas }} tent.
            </span>
          </li>
        </ul>
      </section>
    </div>

    <form method="dialog" class="dialog-scroll-rodape perfil-rodape">
      <button type="submit" class="btn-modo btn-modo-sec btn-largo">
        Fechar
      </button>
    </form>

    <dialog
      ref="dialogoPartidas"
      class="dialog dialog-ranq-info dialog-perfil-info dialog-perfil-partidas"
      aria-labelledby="perfil-partidas-titulo"
      @click="onCliqueForaPartidas"
      @cancel.prevent="fecharPartidas"
    >
      <header class="ranq-info-cabecalho">
        <div>
          <p class="ranq-info-kicker">Histórico</p>
          <h2 id="perfil-partidas-titulo">Últimas {{ LIMITE_PARTIDAS }} partidas</h2>
        </div>
        <BtnFecharDialog :ao-fechar="fecharPartidas" />
      </header>
      <p class="perfil-info-lead">
        Ranqueado e modos solo, da mais recente para a mais antiga.
      </p>
      <ul
        v-if="carregandoPartidas"
        class="perfil-partidas-lista lista-loading"
        aria-busy="true"
      >
        <li v-for="n in 5" :key="n" class="skeleton-linha" />
      </ul>
      <ul v-else class="perfil-partidas-lista">
        <EstadoVazio
          v-if="!ultimasPartidas.length"
          icone="🎮"
          titulo="Nenhuma partida encerrada ainda"
        />
        <li
          v-for="p in ultimasPartidas"
          :key="p.id"
          class="perfil-partida-linha"
          :class="p.venceu ? 'perfil-partida-linha--v' : 'perfil-partida-linha--d'"
        >
          <div class="perfil-partida-esq">
            <span class="perfil-partida-modo">{{ p.modoNome }}</span>
            <span v-if="subtituloPartida(p)" class="perfil-partida-sub">
              {{ subtituloPartida(p) }}
            </span>
            <time class="perfil-partida-data" :datetime="p.dataHora">{{
              formatarDataPartida(p.dataHora)
            }}</time>
          </div>
          <div class="perfil-partida-dir">
            <span
              class="perfil-partida-resultado"
              :class="p.venceu ? 'perfil-partida-resultado--v' : ''"
            >
              {{ p.venceu ? "Vitória" : "Derrota" }}
            </span>
            <span v-if="p.deltaRp != null" class="perfil-partida-rp">
              {{ p.deltaRp >= 0 ? `+${p.deltaRp}` : p.deltaRp }} RP
              <template v-if="p.pontosDepois != null">
                · {{ p.pontosDepois }} RP
              </template>
            </span>
          </div>
        </li>
      </ul>
      <button
        type="button"
        class="btn-modo btn-modo-destaque btn-largo"
        @click="fecharPartidas"
      >
        Fechar
      </button>
    </dialog>

    <dialog
      ref="dialogoRankingInfo"
      class="dialog dialog-ranq-info dialog-perfil-info"
      aria-labelledby="perfil-ranking-info-titulo"
      @click="onCliqueForaRankingInfo"
      @cancel.prevent="fecharRankingInfo"
    >
      <header class="ranq-info-cabecalho">
        <div>
          <p class="ranq-info-kicker">Ranking</p>
          <h2 id="perfil-ranking-info-titulo">Faixas de elo</h2>
        </div>
        <BtnFecharDialog :ao-fechar="fecharRankingInfo" />
      </header>
      <p class="perfil-info-lead">
        Você sobe ou desce de elo conforme ganha ou perde RP nos duelos ranqueados.
      </p>
      <div class="perfil-elos-faixa" aria-hidden="true">
        <EloPill
          v-for="id in ORDEM_ELOS"
          :key="id"
          :rotulo="NOMES_ELO[id]"
          :elo="id"
          :elo-classe="`elo-pill--${id}`"
        />
      </div>
      <p class="perfil-info-nota">
        O ranking global mostra o topo e a sua posição entre
        {{ totalRanqueadosFmt || "—" }} jogadores com partida ranqueada.
      </p>
      <button
        type="button"
        class="btn-modo btn-modo-destaque btn-largo"
        @click="fecharRankingInfo"
      >
        Entendi
      </button>
    </dialog>

    <div
      v-if="store.dialogAvatarAberto"
      class="perfil-avatar-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="perfilAvatarTitulo"
      @click.self="store.fecharDialogAvatar()"
    >
      <div class="perfil-avatar-overlay-painel" @click.stop>
        <header class="perfil-avatar-overlay-cabecalho">
          <h2 id="perfilAvatarTitulo">Escolher avatar</h2>
          <button
            type="button"
            class="btn-icone btn-fechar-dialog"
            aria-label="Fechar"
            @click="store.fecharDialogAvatar()"
          >
            ×
          </button>
        </header>
        <p class="dialog-sub">
          {{
            store.conta?.ehVisitante
              ? "Salvo neste navegador até você criar conta."
              : "Sincronizado com sua conta."
          }}
        </p>
        <p class="dialog-sub perfil-avatar-overlay-dica">
          Todos no mesmo estilo ilustrado — toque para aplicar.
        </p>
        <SeletorAvatares
          :model-value="avatarId"
          :salvando="salvandoAvatar"
          @salvar="onSalvarAvatar"
        />
        <button
          type="button"
          class="btn-modo btn-largo perfil-avatar-overlay-fechar"
          @click="store.fecharDialogAvatar()"
        >
          Fechar
        </button>
      </div>
    </div>
  </dialog>
</template>
