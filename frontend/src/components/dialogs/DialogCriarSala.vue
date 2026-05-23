<script setup>
import { computed, ref } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";

const store = useTermoStore();
const f = store.formCriarSala;
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "criarSala");
const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

const temSenha = computed(() => !!(f.senha && f.senha.trim()));
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-config-premium dialog-criar-premium"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <header class="config-hero">
      <div class="config-hero-texto">
        <p class="config-kicker">Arena</p>
        <h2>Criar sala</h2>
        <p class="config-sub">
          Configure a partida e compartilhe o código com os amigos.
          <span class="config-sub-badge">2 a 8 jogadores</span>
        </p>
      </div>
      <BtnFecharDialog />
    </header>

    <form class="config-form" @submit.prevent="store.submeterCriarSala">
      <div class="dialog-scroll config-corpo">
        <section class="config-secao" aria-labelledby="criar-jogadores">
          <h3 id="criar-jogadores" class="config-secao-titulo">Jogadores</h3>
          <div class="config-card config-card-slider">
            <div class="config-slider-topo">
              <span class="config-slider-label">Máximo na sala</span>
              <span class="config-slider-valor" aria-live="polite">{{ f.maxJogadores }}</span>
            </div>
            <input
              v-model.number="f.maxJogadores"
              type="range"
              class="config-range"
              min="2"
              max="8"
              aria-valuemin="2"
              aria-valuemax="8"
              :aria-valuenow="f.maxJogadores"
            />
            <p class="config-slider-dica">
              A sala aparece na lista pública (com cadeado se tiver senha).
            </p>
          </div>
        </section>

        <section class="config-secao" aria-labelledby="criar-regras">
          <h3 id="criar-regras" class="config-secao-titulo">Regras</h3>
          <div class="config-card config-card-toggles">
            <label class="config-toggle-row">
              <span class="config-toggle-texto">
                <strong>Mesma palavra</strong>
                <small>Todos jogam a palavra igual</small>
              </span>
              <input v-model="f.mesmaPalavra" type="checkbox" class="config-toggle-input" />
              <span class="toggle-ui" aria-hidden="true" />
            </label>
            <label class="config-toggle-row">
              <span class="config-toggle-texto">
                <strong>Ver tabuleiros</strong>
                <small>Vê o progresso dos outros</small>
              </span>
              <input v-model="f.verOutros" type="checkbox" class="config-toggle-input" />
              <span class="toggle-ui" aria-hidden="true" />
            </label>
            <label class="config-toggle-row">
              <span class="config-toggle-texto">
                <strong>Início automático</strong>
                <small>Começa ao atingir 2 jogadores prontos</small>
              </span>
              <input v-model="f.inicioAutoDois" type="checkbox" class="config-toggle-input" />
              <span class="toggle-ui" aria-hidden="true" />
            </label>
          </div>
        </section>

        <section class="config-secao" aria-labelledby="criar-modo">
          <h3 id="criar-modo" class="config-secao-titulo">Modo e tempo</h3>
          <div class="config-card config-card-campos">
            <label class="config-campo">
              <span>Modo da sessão</span>
              <select v-model="f.modoSessao" class="config-select">
                <option value="pontos">Pontos infinitos — maratona</option>
                <option value="vitorias">Primeiro a N vitórias</option>
              </select>
            </label>
            <label v-show="f.modoSessao === 'vitorias'" class="config-campo">
              <span>Vitórias para ganhar</span>
              <select v-model.number="f.metaVitorias" class="config-select">
                <option :value="3">3 vitórias</option>
                <option :value="5">5 vitórias</option>
                <option :value="7">7 vitórias</option>
                <option :value="10">10 vitórias</option>
              </select>
            </label>
            <label class="config-campo">
              <span>Tempo por rodada</span>
              <select v-model.number="f.tempoLimite" class="config-select">
                <option :value="0">Sem limite</option>
                <option :value="60">1 minuto</option>
                <option :value="120">2 minutos</option>
                <option :value="180">3 minutos</option>
                <option :value="300">5 minutos</option>
                <option :value="600">10 minutos</option>
              </select>
            </label>
          </div>
        </section>

        <section class="config-secao" aria-labelledby="criar-senha">
          <h3 id="criar-senha" class="config-secao-titulo">Senha (opcional)</h3>
          <div
            class="config-card config-card-senha"
            :class="{ 'config-card-senha-ativa': temSenha }"
          >
            <p class="config-senha-status">
              <span
                class="config-senha-icone"
                :class="temSenha ? 'travada' : 'aberta'"
                aria-hidden="true"
              />
              {{
                temSenha
                  ? "Sala protegida — quem entrar precisa da senha."
                  : "Sala aberta — basta o código de 6 letras."
              }}
            </p>
            <label class="config-campo config-campo-senha">
              <span>Senha da sala</span>
              <input
                v-model="f.senha"
                type="text"
                maxlength="8"
                class="config-input"
                placeholder="Até 8 caracteres"
                autocomplete="off"
              />
            </label>
          </div>
        </section>
      </div>

      <footer class="config-rodape">
        <button type="submit" class="btn-modo btn-modo-destaque btn-largo config-btn-salvar">
          Criar e entrar
        </button>
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.fecharDialogs()"
        >
          Cancelar
        </button>
      </footer>
    </form>
  </dialog>
</template>
