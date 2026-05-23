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

    <nav class="ajuda-abas" aria-label="Seções da ajuda">
      <button
        type="button"
        class="ajuda-aba"
        :class="{ ativa: aba === 'regras' }"
        @click="aba = 'regras'"
      >
        Regras
      </button>
      <button
        type="button"
        class="ajuda-aba"
        :class="{ ativa: aba === 'modos' }"
        @click="aba = 'modos'"
      >
        Modos
      </button>
      <button
        type="button"
        class="ajuda-aba"
        :class="{ ativa: aba === 'prefs' }"
        @click="aba = 'prefs'"
      >
        Ajustes
      </button>
    </nav>

    <div class="ajuda-corpo">
      <section v-show="aba === 'regras'" class="ajuda-painel">
        <p class="ajuda-lead">
          Adivinhe a palavra de 5 letras em até 6 tentativas. Cada chute revela dicas
          nas letras.
        </p>
        <div class="ajuda-legenda">
          <div class="ajuda-legenda-item">
            <span class="tile demo correto">T</span>
            <div>
              <strong>Verde</strong>
              <span>Letra certa na posição certa</span>
            </div>
          </div>
          <div class="ajuda-legenda-item">
            <span class="tile demo presente">E</span>
            <div>
              <strong>Amarelo</strong>
              <span>Letra existe, em outra posição</span>
            </div>
          </div>
          <div class="ajuda-legenda-item">
            <span class="tile demo ausente">X</span>
            <div>
              <strong>Cinza</strong>
              <span>Letra não está na palavra</span>
            </div>
          </div>
        </div>
        <p class="ajuda-nota">
          Acentos são ignorados na digitação — digite só as letras base (A–Z).
        </p>
      </section>

      <section v-show="aba === 'modos'" class="ajuda-painel">
        <dl class="ajuda-modos-lista">
          <div>
            <dt>Palavra do dia</dt>
            <dd>Uma palavra por dia para todos. Uma tentativa registrada por conta/dia.</dd>
          </div>
          <div>
            <dt>Jogar → Solo</dt>
            <dd>Prática, Dueto (2 palavras) e Quarteto (4 palavras).</dd>
          </div>
          <div>
            <dt>Jogar → Ranqueado</dt>
            <dd>
              Duelo 1v1 com matchmaking, pontos RP e elos (conta com e-mail). Revanche
              disponível após duelo contra outro jogador real.
            </dd>
          </div>
          <div>
            <dt>Nível e XP</dt>
            <dd>
              Conta registrada ganha XP na diária, prática, arena e ranqueada. No início sobe
              rápido; em níveis altos o ganho efetivo cai (~15% do base). Teto de
              <strong>2200 XP/dia</strong> (horário de Brasília). Metas semanais no perfil.
            </dd>
          </div>
          <div>
            <dt>Jogar → Desafio</dt>
            <dd>Mesma palavra por código ou link compartilhado.</dd>
          </div>
          <div>
            <dt>Arena</dt>
            <dd>Salas de 2 a 8 jogadores: maratona de pontos ou corrida a N vitórias.</dd>
          </div>
        </dl>
      </section>

      <section v-show="aba === 'prefs'" class="ajuda-painel ajuda-prefs">
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
          </span>
          <select
            class="ajuda-select"
            :value="store.preferencias.temaModo || (store.preferencias.temaClaro ? 'claro' : 'escuro')"
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
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.mostrarTutorial = true; store.fecharDialogs()"
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
        <p class="ajuda-nota">
          Use se o jogo travar, mensagens repetirem ou a sessão não retomar corretamente.
        </p>
      </section>
    </div>
  </dialog>
</template>
