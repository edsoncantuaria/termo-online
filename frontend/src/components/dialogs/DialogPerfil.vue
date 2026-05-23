<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import EstadoVazio from "../ui/EstadoVazio.vue";
import PerfilNivelAnel from "../ui/PerfilNivelAnel.vue";
import { InicialNick, CorAvatarNick } from "../../utils/jogador.js";
import { BarrasHistorico7d } from "../../utils/progresso.js";
import SeletorAvatares from "../ui/SeletorAvatares.vue";
import EloPill from "../ui/EloPill.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "perfil");
const salvandoAvatar = ref(false);

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

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

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
    class="dialog dialog-perfil"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <div class="perfil-cabecalho perfil-cabecalho--com-nivel">
      <div class="perfil-cabecalho-esq">
        <button
          v-if="store.conta"
          type="button"
          class="perfil-avatar-editar"
          aria-label="Alterar avatar"
          title="Alterar avatar"
          @click.stop="store.abrirDialogAvatar()"
        >
          <PerfilNivelAnel
            v-if="progresso"
            :avatar-id="avatarId"
            :inicial="inicialAvatar"
            :cor-avatar="corAvatar"
            :progresso="progresso"
            tamanho="grande"
          />
          <PerfilNivelAnel
            v-else
            :avatar-id="avatarId"
            :inicial="inicialAvatar"
            :cor-avatar="corAvatar"
            tamanho="grande"
          />
          <span class="perfil-avatar-editar-icone" aria-hidden="true">✎</span>
        </button>
        <div>
          <h2>Seu perfil</h2>
          <p class="dialog-sub">{{ store.nick }}</p>
          <p
            v-if="store.conta?.podeRanqueada"
            class="perfil-cabecalho-ranqueado"
          >
            <EloPill
              :rotulo="eloExibicao"
              :elo="store.conta?.elo"
              :elo-classe="store.conta?.eloClasse"
              :sem-rank="store.conta?.semRank"
              grande
            />
            <strong class="perfil-cabecalho-rp">{{ pontosRp }} RP</strong>
            <span
              v-if="store.minhaPosicaoRanqueada && store.totalRanqueados"
              class="perfil-cabecalho-pos"
            >
              #{{ store.minhaPosicaoRanqueada }} / {{ totalRanqueadosFmt }}
            </span>
          </p>
          <p v-if="progresso" class="perfil-nivel-linha">
            Nível <strong>{{ progresso.nivel }}</strong>
            · {{ progresso.estiloNivel.faixaNome }}
            · {{ progresso.xpTotal.toLocaleString("pt-BR") }} XP total
          </p>
        </div>
      </div>
      <BtnFecharDialog />
    </div>

    <div class="dialog-scroll dialog-scroll-perfil">
    <section v-if="progresso" class="perfil-secao perfil-secao-nivel">
      <h3>Progresso</h3>
      <div class="perfil-xp-barra" role="progressbar" :aria-valuenow="progresso.progressoPct">
        <div class="perfil-xp-preenchido" :style="{ width: `${progresso.progressoPct}%` }" />
      </div>
      <p class="perfil-xp-texto">
        {{ progresso.xpNoNivel }} / {{ progresso.xpProximoNivel }} XP para o nível
        {{ progresso.nivel + 1 }}
      </p>
      <p v-if="progresso.xpCapDiario" class="perfil-xp-meta">
        Ganho hoje: {{ progresso.xpGanhoHoje }} / {{ progresso.xpCapDiario }} XP
        · Eficiência no nível {{ progresso.nivel }}: {{ progresso.multiplicadorXpPct }}%
      </p>
      <details
        v-if="store.historicoRanqueado?.length"
        class="perfil-colapsavel"
        open
      >
        <summary class="perfil-colapsavel-resumo">
          Últimos duelos ranqueados
        </summary>
        <ul class="perfil-colapsavel-corpo perfil-duelos-lista">
          <li
            v-for="(h, i) in store.historicoRanqueado"
            :key="h.id || `${h.dataHora}-${i}`"
            :class="h.venceu ? 'perfil-duelo--v' : 'perfil-duelo--d'"
          >
            <span class="perfil-duelo-oponente">{{ h.nickOponente }}</span>
            <span class="perfil-duelo-delta">
              {{ h.delta >= 0 ? `+${h.delta}` : h.delta }} RP
            </span>
            <span class="perfil-duelo-rp">{{ h.pontosDepois }} RP</span>
          </li>
        </ul>
      </details>

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
      <p v-if="progresso.lembreteMetas" class="perfil-lembrete-metas" role="status">
        {{ progresso.lembreteMetas }}
      </p>
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
                :style="{ width: `${Math.min(100, (100 * m.progresso) / m.meta)}%` }"
              />
            </div>
            <span v-if="m.recompensada" class="perfil-meta-ok">Recompensada</span>
            <span v-else-if="m.concluida" class="perfil-meta-ok">+{{ m.xpRecompensa }} XP</span>
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
            :class="{ 'perfil-badge--ok': b.desbloqueada, 'perfil-badge--bloq': !b.desbloqueada }"
          >
            <span class="perfil-badge-icone" aria-hidden="true">{{ b.icone }}</span>
            <span>
              <strong>{{ b.nome }}</strong>
              <span class="perfil-badge-desc">{{ b.descricao }}</span>
            </span>
          </li>
        </ul>
      </details>
    </section>

    <section class="perfil-secao">
      <h3>Desempenho</h3>
      <div class="stats-grid stats-grid-perfil">
        <div class="stat-item">
          <span class="stat-valor">{{ store.statVitorias }}</span>
          <span class="stat-label">Vitórias</span>
        </div>
        <div class="stat-item">
          <span class="stat-valor">{{ store.statSequencia }}</span>
          <span class="stat-label">Sequência</span>
        </div>
        <div class="stat-item">
          <span class="stat-valor">{{ store.statDiaria }}</span>
          <span class="stat-label">Diária hoje</span>
        </div>
        <div class="stat-item">
          <span class="stat-valor">{{ store.statTaxa }}</span>
          <span class="stat-label">Taxa vitória</span>
        </div>
      </div>
      <p v-if="store.statsExtraTexto" class="perfil-extra">{{ store.statsExtraTexto }}</p>
    </section>

    <section class="perfil-secao">
      <h3>Partidas por modo</h3>
      <p class="dialog-sub perfil-modos-legenda">
        Contagem de partidas <strong>encerradas</strong> em cada modo solo e no ranqueado.
        <template v-if="totalPartidasModos > 0">
          Total solo: {{ totalPartidasModos.toLocaleString("pt-BR") }}.
        </template>
      </p>
      <ul
        v-if="store.carregandoPerfil"
        class="perfil-modos-lista lista-loading"
        aria-busy="true"
      >
        <li v-for="n in 6" :key="n" class="skeleton-linha" />
      </ul>
      <ul v-else class="perfil-modos-lista">
        <li
          v-for="m in partidasPorModo"
          :key="m.modo"
          class="perfil-modo-linha"
          :class="{ 'perfil-modo-linha--vazio': !m.partidas }"
        >
          <span class="perfil-modo-nome">{{ m.nome }}</span>
          <span class="perfil-modo-stats">
            <strong>{{ m.partidas }}</strong>
            <span class="perfil-modo-unidade">
              {{ m.partidas === 1 ? "partida" : "partidas" }}
            </span>
            <span v-if="m.partidas > 0" class="perfil-modo-vitorias">
              · {{ m.vitorias }} {{ m.vitorias === 1 ? "vitória" : "vitórias" }}
            </span>
          </span>
        </li>
      </ul>
    </section>

    <section v-if="store.conta?.podeRanqueada" class="perfil-secao">
      <h3>Ranking ranqueado</h3>
      <p class="dialog-sub">
        Elos: Papelão → Estrela · {{ totalRanqueadosFmt }} jogadores no ranking global
        (topo + sua posição).
      </p>
      <ol v-if="store.carregandoPerfil" class="lista-ranking lista-ranking-perfil lista-loading">
        <li v-for="n in 5" :key="n" class="skeleton-linha" />
      </ol>
      <ol v-else class="lista-ranking lista-ranking-perfil">
        <EstadoVazio
          v-if="!store.rankingRanqueado.length"
          icone="⚔️"
          titulo="Ninguém ranqueou ainda"
        />
        <template
          v-for="item in store.rankingRanqueado"
          :key="item.tipo === 'ellipsis' ? 'gap' : `${item.nick}-${item.posicao}`"
        >
          <li
            v-if="item.tipo === 'ellipsis'"
            class="ranking-ellipsis"
          >···</li>
          <li
            v-else
            :class="{ 'ranking-eu': item.souEu }"
          >
            <span class="ranking-pos">{{ item.posicao }}</span>
            <span class="ranking-nick">{{ item.nick }}</span>
            <span class="ranking-meta">{{ item.eloNome }} · {{ item.pontos }} RP</span>
          </li>
        </template>
      </ol>
    </section>
    <section v-else class="perfil-secao perfil-aviso-conta">
      <p class="dialog-sub">
        Crie uma conta para ver o ranking ranqueado e jogar no modo Ranqueado (em Jogar).
      </p>
      <button type="button" class="btn-modo btn-largo" @click="store.abrirCriarConta()">
        Criar conta
      </button>
    </section>

    <section class="perfil-secao">
      <h3>Palavras do dia</h3>
      <ul v-if="store.carregandoPerfil" class="lista-historico lista-historico-perfil lista-loading">
        <li v-for="n in 4" :key="n" class="skeleton-linha" />
      </ul>
      <ul v-else class="lista-historico lista-historico-perfil">
        <EstadoVazio
          v-if="!store.historicoDiaria.length"
          icone="📅"
          titulo="Nenhuma diária salva"
        />
        <li v-for="item in store.historicoDiaria" :key="item.dataDia">
          <span>{{
            new Date(item.dataDia + "T12:00:00").toLocaleDateString("pt-BR", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })
          }}</span>
          <span :class="item.venceu ? 'historico-ok' : 'historico-falha'">
            {{ item.venceu ? "Venceu" : "Não venceu" }} · {{ item.tentativasUsadas }} tent.
          </span>
        </li>
      </ul>
    </section>
    </div>

    <form method="dialog" class="dialog-scroll-rodape">
      <button type="submit" class="btn-modo btn-largo">Fechar</button>
    </form>

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
