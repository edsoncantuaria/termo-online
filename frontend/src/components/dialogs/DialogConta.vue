<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import { InicialNick, CorAvatarNick, NickExibicao } from "../../utils/jogador.js";
import PerfilNivelAnel from "../ui/PerfilNivelAnel.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "conta");
const modo = ref("entrada");
const nickForm = ref("");
const nickVisitante = ref("");
const emailForm = ref("");
const senhaForm = ref("");
const confirmarSenha = ref("");
const enviando = ref(false);

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

function sincronizarModoConta() {
  modo.value = store.dialogContaForcarRegistro
    ? "registro"
    : store.dialogContaModo || "entrada";
  nickVisitante.value = "";
  if (modo.value === "registro" && store.dialogContaNickSugerido) {
    nickForm.value = store.dialogContaNickSugerido;
  }
}

watch(aberto, (v) => {
  if (v) {
    sincronizarModoConta();
    if (store.conta?.podeRanqueada) store.carregarRankingRanqueado();
  }
});

watch(
  () => store.dialogContaForcarRegistro,
  (forcar) => {
    if (forcar && aberto.value) {
      modo.value = "registro";
      if (store.dialogContaNickSugerido) {
        nickForm.value = store.dialogContaNickSugerido;
      }
    }
  }
);

function normalizarNickVisitante() {
  nickVisitante.value = store.normalizarNickEntrada(nickVisitante.value);
}

const inicialAvatar = computed(() => InicialNick(store.conta?.nick));
const corAvatar = computed(() => CorAvatarNick(store.conta?.nick));
const nickExibicao = computed(() => NickExibicao(store.conta?.nick));
const totalRanqueadosFmt = computed(() =>
  (store.totalRanqueados ?? 0).toLocaleString("pt-BR")
);

async function login() {
  enviando.value = true;
  try {
    await store.authLogin(
      emailForm.value.trim() || nickForm.value,
      senhaForm.value
    );
  } finally {
    enviando.value = false;
  }
}

async function registrar() {
  if (senhaForm.value !== confirmarSenha.value) {
    store.mostrarToast("As senhas não coincidem.", true);
    return;
  }
  enviando.value = true;
  try {
    await store.authRegistrar(
      nickForm.value,
      emailForm.value,
      senhaForm.value
    );
  } finally {
    enviando.value = false;
  }
}

async function visitante() {
  enviando.value = true;
  try {
    await store.authVisitante(nickVisitante.value);
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <dialog
    ref="dialogo"
    class="dialog dialog-conta dialog-conta-premium"
    @click="onCliqueFora"
    @close="fechar"
    @cancel="onCancel"
  >
    <template v-if="store.conta && !store.dialogContaForcarRegistro">
      <header class="auth-hero auth-hero-logado">
        <div class="auth-hero-texto">
          <p class="auth-kicker">Sua conta</p>
          <h2>{{ nickExibicao }}</h2>
          <p v-if="store.conta.ehVisitante" class="auth-sub auth-aviso">
            Visitante: ranking e ranqueado exigem cadastro com e-mail.
          </p>
          <p v-else class="auth-sub">{{ store.conta.email || "—" }}</p>
          <div
            v-if="!store.conta.ehVisitante && store.conta.podeRanqueada"
            class="auth-rank-hero"
          >
            <span class="auth-rank-elo">{{ store.conta.eloNome }}</span>
            <span class="auth-rank-rp">{{ store.conta.pontosRanqueada }} RP</span>
            <span
              v-if="store.minhaPosicaoRanqueada && store.totalRanqueados"
              class="auth-rank-pos"
            >
              Posição #{{ store.minhaPosicaoRanqueada }} de {{ totalRanqueadosFmt }}
            </span>
          </div>
        </div>
        <PerfilNivelAnel
          v-if="store.conta.progresso"
          :inicial="inicialAvatar"
          :cor-avatar="corAvatar"
          :progresso="store.conta.progresso"
          tamanho="grande"
        />
        <span
          v-else
          class="auth-avatar-grande"
          :style="{ background: corAvatar }"
          aria-hidden="true"
        >{{ inicialAvatar }}</span>
        <BtnFecharDialog />
      </header>
      <div class="auth-corpo auth-scroll">
        <button
          v-if="store.conta.ehVisitante"
          type="button"
          class="btn-modo btn-modo-destaque btn-largo"
          @click="store.abrirCriarConta()"
        >
          Criar conta completa
        </button>
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          @click="store.authSair()"
        >
          Sair
        </button>
      </div>
    </template>

    <template v-else>
      <header class="auth-hero">
        <div class="auth-hero-texto">
          <p class="auth-kicker">Termo Online</p>
          <h2>{{ modo === "registro" ? "Criar conta" : "Entrar" }}</h2>
          <p class="auth-sub">
            {{
              modo === "registro"
                ? "Salve progresso, ranqueie e apareça no ranking global."
                : "Use seu e-mail ou nick e a senha cadastrada."
            }}
          </p>
        </div>
        <BtnFecharDialog />
      </header>

      <nav class="auth-abas" aria-label="Entrar ou cadastrar">
        <button
          type="button"
          class="auth-aba"
          :class="{ ativa: modo === 'entrada' }"
          @click="modo = 'entrada'"
        >
          Entrar
        </button>
        <button
          type="button"
          class="auth-aba"
          :class="{ ativa: modo === 'registro' }"
          @click="modo = 'registro'"
        >
          Criar conta
        </button>
      </nav>

      <div class="auth-scroll">
        <section v-if="modo === 'entrada'" class="auth-visitante-topo">
          <label class="auth-campo">
            <span>Seu nome no jogo</span>
            <input
              v-model="nickVisitante"
              type="text"
              maxlength="20"
              class="auth-input"
              autocomplete="nickname"
              placeholder="ex: maria"
              required
              @input="normalizarNickVisitante"
            />
            <span class="auth-dica">
              3–20 caracteres (a–z, números ou _). Se já existir, você ganha Maria1, Maria2…
            </span>
          </label>
          <button
            type="button"
            class="btn-modo btn-modo-sec btn-largo"
            :disabled="enviando || nickVisitante.length < 3"
            @click="visitante"
          >
            Entrar como visitante
          </button>
        </section>

        <form
          class="auth-form"
          :class="{ 'auth-form-com-separador': modo === 'entrada' }"
          @submit.prevent="modo === 'registro' ? registrar() : login()"
        >
          <label v-if="modo === 'registro'" class="auth-campo">
            <span>Nick público</span>
            <input
              v-model="nickForm"
              type="text"
              maxlength="20"
              class="auth-input"
              autocomplete="username"
              placeholder="ex: maria"
              required
              @input="nickForm = nickForm.toLowerCase().replace(/[^a-z0-9_]/g, '')"
            />
            <span class="auth-dica">3–20 caracteres: letras minúsculas, números ou _</span>
          </label>

          <label v-if="modo === 'entrada'" class="auth-campo auth-campo-ou">
            <span>ou entre com sua conta</span>
          </label>

          <label class="auth-campo">
            <span>{{ modo === "registro" ? "E-mail" : "E-mail ou nick" }}</span>
            <input
              v-model="emailForm"
              :type="modo === 'registro' ? 'email' : 'text'"
              class="auth-input"
              :autocomplete="modo === 'registro' ? 'email' : 'username'"
              :placeholder="modo === 'registro' ? 'voce@email.com' : 'e-mail ou nick'"
              required
            />
          </label>

          <label class="auth-campo">
            <span>Senha</span>
            <input
              v-model="senhaForm"
              type="password"
              class="auth-input"
              :autocomplete="modo === 'registro' ? 'new-password' : 'current-password'"
              placeholder="Mínimo 6 caracteres"
              required
              minlength="6"
            />
          </label>

          <label v-if="modo === 'registro'" class="auth-campo">
            <span>Confirmar senha</span>
            <input
              v-model="confirmarSenha"
              type="password"
              class="auth-input"
              autocomplete="new-password"
              required
              minlength="6"
            />
          </label>

          <button
            type="submit"
            class="btn-modo btn-modo-destaque btn-largo auth-submit"
            :disabled="enviando"
          >
            {{
              enviando
                ? "Aguarde…"
                : modo === "registro"
                  ? "Criar conta"
                  : "Entrar"
            }}
          </button>
        </form>

        <ul
          v-if="modo === 'registro'"
          class="auth-beneficios"
          aria-label="Vantagens da conta"
        >
          <li>Ranking ranqueado e duelo 1v1</li>
          <li>Nick fixo em salas e arena</li>
          <li>Histórico e estatísticas no perfil</li>
        </ul>

        <p v-if="modo === 'entrada'" class="auth-link-registro">
          Ainda não tem conta?
          <button type="button" class="auth-link-btn" @click="modo = 'registro'">
            Criar conta
          </button>
        </p>
      </div>
    </template>
  </dialog>
</template>
