<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "jogar");
const aba = ref("solo");

function tentarFecharDialog() {
  if (store.filaRanqueadaTravada && !store.filaRanqueadaPodeCancelar) return;
  if (store.filaRanqueadaTravada) {
    store.pararFilaRanqueada();
    return;
  }
  store.fecharDialogs();
}

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  tentarFecharDialog
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

const contaRegistrada = computed(() => store.contaRegistrada);
const buscaAtiva = computed(() => store.filaRanqueadaTravada);
const podeCancelar = computed(() => store.filaRanqueadaPodeCancelar);
const faseConectando = computed(() => store.filaFase === "conectando");

const tituloBusca = computed(() => {
  if (faseConectando.value) return "Oponente encontrado!";
  const f = store.filaFase;
  if (f === "encontrando") return "Combinando duelo…";
  if (f === "entrando") return "Quase lá…";
  return "Buscando adversário";
});

const subtituloBusca = computed(() => {
  if (faseConectando.value) {
    return store.filaMensagem || "Carregando a partida…";
  }
  return (
    store.filaMensagem ||
    "Expandindo a janela de RP para achar um oponente equilibrado"
  );
});

function mudarAba(id) {
  if (buscaAtiva.value) return;
  aba.value = id;
}

function onCliqueForaTravado(ev) {
  if (buscaAtiva.value) {
    ev.preventDefault();
    ev.stopPropagation();
    return;
  }
  onCliqueFora(ev);
}

function onCancelTravado(ev) {
  if (buscaAtiva.value && !podeCancelar.value) {
    ev.preventDefault();
    return;
  }
  if (buscaAtiva.value && podeCancelar.value) {
    ev.preventDefault();
    store.pararFilaRanqueada();
    return;
  }
  onCancel(ev);
}

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

async function jogarDesafio() {
  const cod = store.codigoDesafio.trim().toUpperCase();
  if (!cod) {
    store.mostrarToast("Informe o código da sala", true);
    return;
  }
  store.fecharDialogs();
  if (cod.length === 6) {
    const R = await store.executarEntradaSala(cod);
    if (R.ok) return;
    if (R.precisaSenha) {
      store.mostrarAvisoSenhaConviteSala(cod);
      return;
    }
    store.tratarErroEntradaSala(R.mensagem);
    return;
  }
  store.iniciarModo("desafio", { codigoDesafio: cod });
}

function buscarRanqueado() {
  if (!store.exigirContaRegistrada()) return;
  aba.value = "ranqueado";
  store.entrarFilaRanqueada();
}

function clicarAbaRanqueado() {
  if (buscaAtiva.value) return;
  aba.value = "ranqueado";
}
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-jogar dialog-jogar-premium"
    :class="{ 'dialog-jogar--busca': buscaAtiva }"
    @click="onCliqueForaTravado"
    @close="fechar"
    @cancel="onCancelTravado"
  >
    <header class="jogar-hero">
      <div class="jogar-hero-texto">
        <p class="jogar-kicker">Escolha seu modo</p>
        <h2>Jogar</h2>
        <p>Treino solo, duelo ranqueado ou desafio com amigos.</p>
      </div>
      <BtnFecharDialog
        v-if="!buscaAtiva || podeCancelar"
        :ao-fechar="tentarFecharDialog"
      />
    </header>

    <nav
      class="jogar-abas"
      :class="{ 'jogar-abas--travadas': buscaAtiva }"
      aria-label="Categorias de jogo"
    >
      <button
        type="button"
        class="jogar-aba"
        :class="{ ativa: aba === 'solo' }"
        :disabled="buscaAtiva"
        @click="mudarAba('solo')"
      >
        <span class="jogar-aba-icone" aria-hidden="true">◎</span>
        Solo
      </button>
      <button
        type="button"
        class="jogar-aba jogar-aba-ranqueado"
        :class="{
          ativa: aba === 'ranqueado',
          'jogar-aba--bloqueada': !contaRegistrada && !buscaAtiva,
        }"
        :disabled="buscaAtiva && !faseConectando"
        @click="clicarAbaRanqueado"
      >
        <span class="jogar-aba-icone" aria-hidden="true">⚔</span>
        Ranqueado
      </button>
      <button
        type="button"
        class="jogar-aba"
        :class="{ ativa: aba === 'desafio' }"
        :disabled="buscaAtiva"
        @click="mudarAba('desafio')"
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
        <article
          class="jogar-ranqueado-card"
          :class="{
            'jogar-ranqueado-card--busca': buscaAtiva,
            'jogar-ranqueado-card--bloqueado': !contaRegistrada && !buscaAtiva,
          }"
        >
          <div v-if="!buscaAtiva" class="jogar-ranqueado-topo">
            <div>
              <h3>Duelo 1v1 ranqueado</h3>
              <p>Matchmaking por RP · partida validada no servidor</p>
            </div>
            <div v-if="contaRegistrada" class="jogar-ranqueado-stats">
              <span class="jogar-elo-pill">{{ eloExibicao }}</span>
              <span class="jogar-rp">{{ pontosExibicao }} RP</span>
              <span v-if="posicaoExibicao && store.totalRanqueados" class="jogar-posicao">
                #{{ posicaoExibicao }} / {{ totalRanqueadosFmt }}
              </span>
            </div>
          </div>

          <div v-if="!contaRegistrada && !buscaAtiva" class="jogar-ranqueado-bloqueado">
            <p class="modo-explicacao">
              Você entra na <strong>fila online</strong> e o jogo busca um oponente com
              pontuação parecida (RP). Cada vitória ou derrota altera seu RP e sua
              <strong>faixa de elo</strong> (Madeira → Estrela). O histórico fica na sua
              conta e no ranking global.
            </p>
            <ul class="jogar-ranqueado-lista">
              <li>Vitória: cerca de <strong>+16 a +20 RP</strong></li>
              <li>Derrota: cerca de <strong>−8 a −12 RP</strong> (conforme o adversário)</li>
              <li>Visitante não ranqueia — precisa de conta com e-mail</li>
            </ul>
            <div class="modo-acoes-conta">
              <button
                type="button"
                class="btn-modo btn-largo"
                @click="store.abrirLoginConta()"
              >
                Entrar
              </button>
              <button
                type="button"
                class="btn-modo btn-modo-sec btn-largo"
                @click="store.abrirCriarConta()"
              >
                Criar conta
              </button>
            </div>
          </div>

          <template v-else-if="contaRegistrada">
            <div
              v-if="buscaAtiva"
              class="jogar-mm"
              :class="{ 'jogar-mm--conectando': faseConectando }"
              role="status"
              aria-live="polite"
            >
              <div class="jogar-mm-visual" aria-hidden="true">
                <span class="jogar-mm-anel jogar-mm-anel--1" />
                <span class="jogar-mm-anel jogar-mm-anel--2" />
                <span class="jogar-mm-anel jogar-mm-anel--3" />
                <span class="jogar-mm-nucleo">
                  <span v-if="faseConectando" class="jogar-mm-icone">✓</span>
                  <span v-else class="jogar-mm-icone">⚔</span>
                </span>
                <span
                  v-for="n in 6"
                  :key="n"
                  class="jogar-mm-orbita"
                  :style="{ '--i': n }"
                />
              </div>

              <h3 class="jogar-mm-titulo">{{ tituloBusca }}</h3>
              <p class="jogar-mm-sub">{{ subtituloBusca }}</p>

              <div v-if="!faseConectando" class="jogar-mm-detalhes">
                <div class="jogar-fila-stats">
                  <span v-if="store.filaJogadoresOnline != null">
                    {{ store.filaJogadoresOnline }} online
                  </span>
                  <span v-if="store.filaJogadoresNaFila > 0">
                    {{ store.filaJogadoresNaFila }} na fila
                  </span>
                  <span v-if="store.filaSegundos != null">{{ store.filaSegundos }}s</span>
                </div>
                <p v-if="store.filaBusca" class="jogar-fila-janela">
                  Janela <strong>±{{ store.filaBusca.janelaRp }} RP</strong>
                  ({{ store.filaBusca.rpMinimo }}–{{ store.filaBusca.rpMaximo }})
                </p>
                <div
                  v-if="store.filaBusca?.aberturaPct != null"
                  class="jogar-fila-progresso"
                  role="progressbar"
                  :aria-valuenow="store.filaBusca.aberturaPct"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div
                    class="jogar-fila-progresso-fill"
                    :style="{ width: `${store.filaBusca.aberturaPct}%` }"
                  />
                </div>
              </div>

              <p v-else class="jogar-mm-carregando">Abrindo o duelo…</p>

              <button
                v-if="podeCancelar"
                type="button"
                class="btn-modo btn-modo-sec btn-largo jogar-mm-cancelar"
                @click="store.pararFilaRanqueada()"
              >
                Cancelar busca
              </button>
            </div>

            <template v-else>
              <button
                type="button"
                class="btn-modo btn-modo-destaque btn-largo btn-jogar-ranqueado"
                @click="buscarRanqueado"
              >
                Buscar partida ranqueada
              </button>
              <p class="jogar-ranqueado-regras">
                Vitória <strong>+16~+20 RP</strong> · Derrota <strong>−8~−12 RP</strong> conforme o oponente.
                Durante o duelo você só vê se o rival já chutou.
              </p>
            </template>
          </template>
        </article>

        <div
          v-show="!buscaAtiva"
          class="jogar-elos-faixa"
          aria-label="Faixas de elo"
        >
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
          <p>Sala para até 4 jogadores — primeiro a 3 vitórias na rodada ganha.</p>
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
