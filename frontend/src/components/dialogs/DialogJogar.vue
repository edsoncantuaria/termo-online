<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "jogar");
const aba = ref("solo");

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

const linkDesafio = computed(() =>
  store.codigoDesafio.trim()
    ? store.linkDesafio(store.codigoDesafio)
    : ""
);

const eloExibicao = computed(() => store.conta?.eloNome || "—");
const pontosExibicao = computed(() => store.conta?.pontosRanqueada ?? 0);
const posicaoExibicao = computed(() => store.minhaPosicaoRanqueada);
const totalRanqueadosFmt = computed(() =>
  (store.totalRanqueados ?? 0).toLocaleString("pt-BR")
);

const tituloBusca = computed(() => {
  const f = store.filaFase;
  if (f === "encontrando") return "Oponente encontrado na fila";
  if (f === "entrando") return "Iniciando partida…";
  return "Procurando oponente…";
});

watch(aberto, (v) => {
  if (v) {
    store.carregarRankingRanqueado();
    if (store.filaRanqueada) aba.value = "ranqueado";
  }
});

function jogarModo(modo) {
  store.fecharDialogs();
  store.iniciarModo(modo, { dificuldade: store.dificuldade });
}

function jogarDesafio() {
  const cod = store.codigoDesafio.trim().toUpperCase();
  if (!cod) {
    store.mostrarToast("Informe o código do desafio", true);
    return;
  }
  store.fecharDialogs();
  store.iniciarModo("desafio", { codigoDesafio: cod });
}

function buscarRanqueado() {
  if (!store.exigirContaRegistrada()) return;
  aba.value = "ranqueado";
  store.entrarFilaRanqueada();
}
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-jogar dialog-jogar-premium"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <header class="jogar-hero">
      <div class="jogar-hero-texto">
        <p class="jogar-kicker">Escolha seu modo</p>
        <h2>Jogar</h2>
        <p>Treino solo, duelo ranqueado ou desafio com amigos.</p>
      </div>
      <BtnFecharDialog />
    </header>

    <nav class="jogar-abas" aria-label="Categorias de jogo">
      <button
        type="button"
        class="jogar-aba"
        :class="{ ativa: aba === 'solo' }"
        @click="aba = 'solo'"
      >
        <span class="jogar-aba-icone" aria-hidden="true">◎</span>
        Solo
      </button>
      <button
        type="button"
        class="jogar-aba jogar-aba-ranqueado"
        :class="{ ativa: aba === 'ranqueado' }"
        @click="aba = 'ranqueado'"
      >
        <span class="jogar-aba-icone" aria-hidden="true">⚔</span>
        Ranqueado
      </button>
      <button
        type="button"
        class="jogar-aba"
        :class="{ ativa: aba === 'desafio' }"
        @click="aba = 'desafio'"
      >
        <span class="jogar-aba-icone" aria-hidden="true">⎘</span>
        Desafio
      </button>
    </nav>

    <div class="jogar-corpo">
      <!-- Solo -->
      <section v-show="aba === 'solo'" class="jogar-painel" aria-label="Modos solo">
        <div class="jogar-grid-modos">
          <button type="button" class="jogar-modo-card jogar-modo-pratica" @click="jogarModo('pratica')">
            <span class="jogar-modo-icone" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="28" height="28"><path fill="currentColor" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8zm-1 3v6l5 3 .9-1.45-4.4-2.55V7z"/></svg>
            </span>
            <strong>Prática</strong>
            <span>Palavras ilimitadas · treine no seu ritmo</span>
          </button>
          <button type="button" class="jogar-modo-card jogar-modo-dueto" @click="jogarModo('dueto')">
            <span class="jogar-modo-icone" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="28" height="28"><path fill="currentColor" d="M4 6h6v12H4zm10 0h6v12h-6z" opacity=".5"/><path fill="currentColor" d="M4 6h6v12H4zm10 0h6v12h-6z"/></svg>
            </span>
            <strong>Dueto</strong>
            <span>2 palavras · 7 tentativas</span>
          </button>
          <button type="button" class="jogar-modo-card jogar-modo-quarteto" @click="jogarModo('quarteto')">
            <span class="jogar-modo-icone" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="28" height="28"><path fill="currentColor" d="M2 6h4v12H2zm6 0h4v12H8zm6 0h4v12h-4zm6 0h4v12h-4z"/></svg>
            </span>
            <strong>Quarteto</strong>
            <span>4 palavras · 9 tentativas</span>
          </button>
        </div>
        <label class="jogar-dificuldade">
          <span>Dificuldade na prática</span>
          <select v-model="store.dificuldade" class="input-redondo select-redondo">
            <option value="normal">Normal</option>
            <option value="dificil">Difícil</option>
          </select>
        </label>
      </section>

      <!-- Ranqueado -->
      <section v-show="aba === 'ranqueado'" class="jogar-painel" aria-label="Modo ranqueado">
        <article class="jogar-ranqueado-card">
          <div class="jogar-ranqueado-topo">
            <div>
              <h3>Duelo 1v1</h3>
              <p>Matchmaking por pontos · elo validado no servidor</p>
            </div>
            <div v-if="store.conta?.podeRanqueada" class="jogar-ranqueado-stats">
              <span class="jogar-elo-pill">{{ eloExibicao }}</span>
              <span class="jogar-rp">{{ pontosExibicao }} RP</span>
              <span v-if="posicaoExibicao && store.totalRanqueados" class="jogar-posicao">
                #{{ posicaoExibicao }} / {{ totalRanqueadosFmt }}
              </span>
            </div>
          </div>

          <div v-if="!store.conta?.podeRanqueada" class="jogar-ranqueado-cta">
            <p>Crie uma conta para ranquear e subir de elo.</p>
            <button type="button" class="btn-modo btn-largo" @click="store.abrirCriarConta()">
              Criar conta
            </button>
          </div>

          <template v-else>
            <div v-if="store.filaRanqueada" class="jogar-buscando" role="status" aria-live="polite">
              <span class="jogar-spinner" aria-hidden="true" />
              <p><strong>{{ tituloBusca }}</strong></p>
              <p v-if="store.filaMensagem" class="jogar-fila-msg">{{ store.filaMensagem }}</p>
              <div class="jogar-fila-stats">
                <span>{{ store.filaJogadoresOnline }} jogadores online</span>
                <span v-if="store.filaJogadoresNaFila > 0">
                  {{ store.filaJogadoresNaFila }} na fila agora
                </span>
                <span v-if="store.filaSegundos != null">{{ store.filaSegundos }}s</span>
              </div>
              <p v-if="store.filaBusca" class="jogar-fila-janela">
                Busca: <strong>±{{ store.filaBusca.janelaRp }} RP</strong>
                ({{ store.filaBusca.rpMinimo }}–{{ store.filaBusca.rpMaximo }})
              </p>
              <ul v-if="store.filaPreview.length" class="jogar-fila-lista">
                <li
                  v-for="p in store.filaPreview"
                  :key="p.nick"
                  :class="{ 'jogar-fila-destaque': p.destacado }"
                >
                  <span class="jogar-fila-nick">{{ p.nick }}</span>
                  <span class="jogar-fila-meta">{{ p.eloNome }} · {{ p.pontos }} RP</span>
                  <span class="jogar-fila-badge">na fila</span>
                </li>
              </ul>
              <button
                type="button"
                class="btn-modo btn-modo-sec btn-largo"
                @click="store.pararFilaRanqueada()"
              >
                Cancelar busca
              </button>
            </div>
            <button
              v-else
              type="button"
              class="btn-modo btn-modo-destaque btn-largo btn-jogar-ranqueado"
              @click="buscarRanqueado"
            >
              Buscar partida ranqueada
            </button>
            <p class="jogar-ranqueado-regras">
              Vitória <strong>+16~+20 RP</strong> · Derrota <strong>−8~−12 RP</strong> conforme o oponente
            </p>
          </template>
        </article>

        <div class="jogar-elos-faixa" aria-label="Faixas de elo">
          <span>Madeira</span>
          <span>Papelão</span>
          <span>Ferro</span>
          <span>Bronze</span>
          <span>Ouro</span>
          <span>Platina</span>
          <span>Diamante</span>
          <span class="jogar-elo-estrela">Estrela</span>
        </div>
      </section>

      <!-- Desafio -->
      <section v-show="aba === 'desafio'" class="jogar-painel" aria-label="Desafio com amigos">
        <article class="jogar-desafio-card">
          <h3>Desafio com amigos</h3>
          <p>Mesma palavra para todos que usarem o código ou o link.</p>
          <div class="desafio-linha">
            <input
              v-model="store.codigoDesafio"
              type="text"
              maxlength="8"
              placeholder="Código"
              class="input-redondo input-codigo"
              @input="store.codigoDesafio = store.codigoDesafio.toUpperCase()"
            />
            <button type="button" class="btn-modo btn-modo-destaque" @click="jogarDesafio">
              Jogar
            </button>
          </div>
          <button type="button" class="btn-modo btn-modo-sec btn-largo" @click="store.criarDesafio()">
            Criar desafio e copiar link
          </button>
          <p v-if="linkDesafio" class="desafio-link-preview">
            <button
              type="button"
              class="btn-link-home"
              @click="store.copiarTexto(linkDesafio, 'Link copiado!')"
            >
              Copiar link do desafio
            </button>
          </p>
        </article>
      </section>
    </div>
  </dialog>
</template>
