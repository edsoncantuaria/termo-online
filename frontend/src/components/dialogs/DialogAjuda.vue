<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "ajuda");
const aba = ref("regras");

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

const dicasCores = [
  {
    id: "correto",
    letra: "T",
    classe: "correto",
    titulo: "Verde",
    texto: "Letra certa, no lugar certo.",
  },
  {
    id: "presente",
    letra: "E",
    classe: "presente",
    titulo: "Amarelo",
    texto: "A letra existe na palavra, mas em outra posição.",
  },
  {
    id: "ausente",
    letra: "X",
    classe: "ausente",
    titulo: "Cinza",
    texto: "A letra não aparece na palavra.",
  },
];

const gruposModos = [
  {
    titulo: "Todo dia",
    itens: [
      {
        id: "diaria",
        icone: "📅",
        nome: "Palavra do dia",
        desc: "A mesma palavra para todo mundo. Uma partida por conta a cada dia.",
        tag: "Diário",
      },
    ],
  },
  {
    titulo: "No seu ritmo",
    itens: [
      {
        id: "pratica",
        icone: "🎯",
        nome: "Prática",
        desc: "Uma palavra por partida, quantas vezes quiser. Ótimo para aquecer.",
      },
      {
        id: "multipalavra",
        icone: "🔤",
        nome: "Dueto e Quarteto",
        desc: "Duas ou quatro palavras na mesma rodada — acerte todas para vencer.",
      },
    ],
  },
  {
    titulo: "Com outras pessoas",
    itens: [
      {
        id: "ranqueado",
        icone: "⚔️",
        nome: "Ranqueado 1v1",
        desc: "Duelo automático. Ganha ou perde pontos RP e muda de elo. Exige conta com e-mail.",
        tag: "RP",
      },
      {
        id: "treino",
        icone: "🏋️",
        nome: "Treino ranqueado",
        desc: "Mesmo duelo, sem alterar seu RP. Aparece no perfil como Treino!",
        tag: "Sem RP",
      },
      {
        id: "desafio",
        icone: "🔗",
        nome: "Desafio",
        desc: "Gere um código ou link — todos jogam a mesma palavra ao mesmo tempo.",
      },
      {
        id: "arena",
        icone: "🏟️",
        nome: "Arena",
        desc: "Salas de 2 a 8 jogadores: maratona de pontos ou corrida até N vitórias.",
        tag: "Sala",
      },
    ],
  },
  {
    titulo: "Progressão",
    itens: [
      {
        id: "xp",
        icone: "⭐",
        nome: "Nível e XP",
        desc: "Conta registrada ganha XP ao jogar. Limite de 2200 XP/dia (horário de Brasília). Metas semanais no perfil.",
      },
    ],
  },
];
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-ajuda dialog-ajuda-premium"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <header class="ajuda-hero">
      <div>
        <p class="ajuda-kicker">Central de ajuda</p>
        <h2>Como jogar</h2>
      </div>
      <BtnFecharDialog />
    </header>

    <nav class="ajuda-abas ajuda-abas--pills" aria-label="Seções da ajuda">
      <button
        type="button"
        class="ajuda-aba ajuda-aba--pill"
        :class="{ ativa: aba === 'regras' }"
        :aria-current="aba === 'regras' ? 'page' : undefined"
        @click="aba = 'regras'"
      >
        Regras
      </button>
      <button
        type="button"
        class="ajuda-aba ajuda-aba--pill"
        :class="{ ativa: aba === 'modos' }"
        :aria-current="aba === 'modos' ? 'page' : undefined"
        @click="aba = 'modos'"
      >
        Modos
      </button>
      <button
        type="button"
        class="ajuda-aba ajuda-aba--pill"
        :class="{ ativa: aba === 'prefs' }"
        :aria-current="aba === 'prefs' ? 'page' : undefined"
        @click="aba = 'prefs'"
      >
        Ajustes
      </button>
    </nav>

    <div class="ajuda-corpo">
      <section v-show="aba === 'regras'" class="ajuda-painel">
        <p class="ajuda-lead">
          Descubra a palavra secreta de <strong>5 letras</strong> em até
          <strong>6 tentativas</strong>.
        </p>
        <ol class="ajuda-passos">
          <li>Digite um palpite válido do dicionário e confirme.</li>
          <li>Use as cores para chegar mais perto na próxima tentativa.</li>
        </ol>
        <ul class="ajuda-dicas" aria-label="Significado das cores">
          <li
            v-for="dica in dicasCores"
            :key="dica.id"
            class="ajuda-card ajuda-card--compacto"
          >
            <span
              class="tile demo ajuda-card-tile"
              :class="dica.classe"
              aria-hidden="true"
            >{{ dica.letra }}</span>
            <div class="ajuda-card-corpo">
              <strong class="ajuda-card-nome">{{ dica.titulo }}</strong>
              <p class="ajuda-card-desc">{{ dica.texto }}</p>
            </div>
          </li>
        </ul>
        <p class="ajuda-nota">
          Acentos não entram na digitação — use só as letras de A a Z.
        </p>
      </section>

      <section v-show="aba === 'modos'" class="ajuda-painel">
        <p class="ajuda-lead">
          Escolha como quer jogar: sozinho, com amigos ou contra outros jogadores.
        </p>
        <div class="ajuda-modos-grupos">
          <section
            v-for="grupo in gruposModos"
            :key="grupo.titulo"
            class="ajuda-grupo"
          >
            <h3 class="ajuda-grupo-titulo">{{ grupo.titulo }}</h3>
            <ul class="ajuda-cards">
              <li
                v-for="item in grupo.itens"
                :key="item.id"
                class="ajuda-card"
              >
                <span class="ajuda-card-icone" aria-hidden="true">{{
                  item.icone
                }}</span>
                <div class="ajuda-card-corpo">
                  <div class="ajuda-card-topo">
                    <strong class="ajuda-card-nome">{{ item.nome }}</strong>
                    <span
                      v-if="item.tag"
                      class="ajuda-card-tag"
                      :class="`ajuda-card-tag--${item.id}`"
                    >{{ item.tag }}</span>
                  </div>
                  <p class="ajuda-card-desc">{{ item.desc }}</p>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </section>

      <section v-show="aba === 'prefs'" class="ajuda-painel ajuda-prefs">
        <p class="ajuda-lead">Personalize som, cores e desempenho do app.</p>
        <div class="ajuda-prefs-bloco">
          <label class="ajuda-toggle">
            <input
              type="checkbox"
              :checked="!!store.preferencias.som"
              @change="store.definirPreferenciaSom($event.target.checked)"
            />
            <span class="ajuda-toggle-ui" />
            <span class="ajuda-toggle-texto">
              <strong>Sons</strong>
              <small>Teclado, chutes e feedback</small>
            </span>
          </label>
          <label v-if="store.preferencias.som" class="ajuda-volume">
            <span>Volume</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              :value="store.preferencias.volume ?? 0.75"
              @input="store.definirPreferenciaVolume($event.target.value)"
            />
          </label>
        </div>
        <div class="ajuda-prefs-bloco">
          <label class="ajuda-toggle">
            <input
              type="checkbox"
              :checked="!!store.preferencias.daltonismo"
              @change="store.definirPreferenciaDaltonismo($event.target.checked)"
            />
            <span class="ajuda-toggle-ui" />
            <span class="ajuda-toggle-texto">
              <strong>Modo daltônico</strong>
              <small>Símbolos nas peças</small>
            </span>
          </label>
          <label class="ajuda-campo">
            <span class="ajuda-toggle-texto">
              <strong>Tema</strong>
              <small>Claro, escuro ou seguir o sistema</small>
            </span>
            <select
              class="ajuda-select"
              :value="
                store.preferencias.temaModo ||
                (store.preferencias.temaClaro ? 'claro' : 'escuro')
              "
              @change="store.definirPreferenciaTemaModo($event.target.value)"
            >
              <option value="sistema">Sistema</option>
              <option value="escuro">Escuro</option>
              <option value="claro">Claro</option>
            </select>
          </label>
          <label class="ajuda-toggle">
            <input
              type="checkbox"
              :checked="!!store.preferencias.reduzirAnimacao"
              @change="store.definirPreferenciaAnimacao($event.target.checked)"
            />
            <span class="ajuda-toggle-ui" />
            <span class="ajuda-toggle-texto">
              <strong>Reduzir animação</strong>
              <small>Menos movimento nas peças</small>
            </span>
          </label>
        </div>
        <div class="ajuda-prefs-acoes">
          <button
            type="button"
            class="btn-modo btn-modo-sec btn-largo"
            @click="
              store.mostrarTutorial = true;
              store.fecharDialogs();
            "
          >
            Rever tutorial inicial
          </button>
          <button
            type="button"
            class="btn-modo btn-modo-sec btn-largo"
            @click="store.confirmarLimparCache()"
          >
            Limpar cache local
          </button>
        </div>
        <p class="ajuda-nota">
          Atualizações costumam aplicar ao reabrir a aba. Limpe o cache só se
          travar ou a sessão não retomar.
        </p>
      </section>
    </div>
  </dialog>
</template>
