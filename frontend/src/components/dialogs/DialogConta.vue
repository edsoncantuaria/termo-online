<script setup>
import { computed, ref, watch } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useDialogoNativo } from "../../composables/useDialogoNativo.js";
import BtnFecharDialog from "./BtnFecharDialog.vue";
import { InicialNick, CorAvatarNick, NickExibicao } from "../../utils/jogador.js";
import {
  NormalizarNick,
  ValidarNick,
  ValidarLogin,
  ValidarRegistro,
} from "../../utils/validacao-auth.js";
import PerfilNivelAnel from "../ui/PerfilNivelAnel.vue";

const store = useTermoStore();
const dialogo = ref(null);
const aberto = computed(() => store.dialogAberto === "conta");
const passo = ref("visitante");
const modo = ref("entrada");
const nickForm = ref("");
const nickVisitante = ref("");
const emailForm = ref("");
const senhaForm = ref("");
const confirmarSenha = ref("");
const enviando = ref(false);
const erroVisitante = ref("");
const erroConta = ref("");

const { fechar, onCliqueFora, onCancel } = useDialogoNativo(
  dialogo,
  aberto,
  () => store.fecharDialogs()
);

function sincronizarModoConta() {
  const forcarRegistro = store.dialogContaForcarRegistro;
  const modoStore = store.dialogContaModo || "entrada";
  if (forcarRegistro || modoStore === "registro") {
    passo.value = "conta";
    modo.value = "registro";
  } else {
    passo.value = "visitante";
    modo.value = "entrada";
  }
  nickVisitante.value = "";
  limparErros();
  if (modo.value === "registro" && store.dialogContaNickSugerido) {
    nickForm.value = store.dialogContaNickSugerido;
  }
}

function abrirPassoConta(modoInicial = "entrada") {
  passo.value = "conta";
  modo.value = modoInicial;
}

function voltarPassoVisitante() {
  passo.value = "visitante";
}

watch(aberto, (v) => {
  if (v) {
    sincronizarModoConta();
    if (store.conta?.podeRanqueada) store.carregarRankingRanqueado();
  } else {
    passo.value = "visitante";
  }
});

watch(
  () => store.dialogContaForcarRegistro,
  (forcar) => {
    if (forcar && aberto.value) {
      passo.value = "conta";
      modo.value = "registro";
      if (store.dialogContaNickSugerido) {
        nickForm.value = store.dialogContaNickSugerido;
      }
    }
  }
);

function limparErros() {
  erroVisitante.value = "";
  erroConta.value = "";
}

function normalizarNickVisitante() {
  nickVisitante.value = NormalizarNick(nickVisitante.value);
  erroVisitante.value = "";
}

const avisoNickCurto = computed(() => {
  if (erroVisitante.value) return "";
  const n = NormalizarNick(nickVisitante.value);
  if (!n || n.length >= 3) return "";
  return `Faltam ${3 - n.length} caractere(s) — mínimo 3 (ex.: ed → ed1).`;
});

const inicialAvatar = computed(() => InicialNick(store.conta?.nick));
const corAvatar = computed(() => CorAvatarNick(store.conta?.nick));
const avatarId = computed(() => store.avatarIdEfetivo());
const nickExibicao = computed(() => NickExibicao(store.conta?.nick));
const totalRanqueadosFmt = computed(() =>
  (store.totalRanqueados ?? 0).toLocaleString("pt-BR")
);

async function login() {
  limparErros();
  const V = ValidarLogin(emailForm.value.trim(), senhaForm.value);
  if (!V.ok) {
    erroConta.value = V.mensagem;
    store.mostrarToast(V.mensagem, true);
    return;
  }
  enviando.value = true;
  try {
    const R = await store.authLogin(emailForm.value.trim(), senhaForm.value);
    if (R?.ok === false) erroConta.value = R.mensagem || "";
  } finally {
    enviando.value = false;
  }
}

async function registrar() {
  limparErros();
  const V = ValidarRegistro(
    nickForm.value,
    emailForm.value,
    senhaForm.value,
    confirmarSenha.value
  );
  if (!V.ok) {
    erroConta.value = V.mensagem;
    store.mostrarToast(V.mensagem, true);
    return;
  }
  enviando.value = true;
  try {
    const R = await store.authRegistrar(
      V.nick,
      emailForm.value,
      senhaForm.value,
      confirmarSenha.value
    );
    if (R?.ok === false) erroConta.value = R.mensagem || "";
  } finally {
    enviando.value = false;
  }
}

async function visitante() {
  limparErros();
  const V = ValidarNick(nickVisitante.value);
  if (!V.ok) {
    erroVisitante.value = V.mensagem;
    store.mostrarToast(V.mensagem, true);
    return;
  }
  nickVisitante.value = V.nick;
  enviando.value = true;
  try {
    const R = await store.authVisitante(V.nick);
    if (R?.ok === false) erroVisitante.value = R.mensagem || "";
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
          :avatar-id="avatarId"
          :inicial="inicialAvatar"
          :cor-avatar="corAvatar"
          :progresso="store.conta.progresso"
          tamanho="grande"
        />
        <PerfilNivelAnel
          v-else
          :avatar-id="avatarId"
          :inicial="inicialAvatar"
          :cor-avatar="corAvatar"
          tamanho="grande"
        />
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
          <h2>
            {{
              passo === "visitante"
                ? "Jogar"
                : modo === "registro"
                  ? "Criar conta"
                  : "Entrar"
            }}
          </h2>
          <p class="auth-sub">
            {{
              passo === "visitante"
                ? "Escolha um nick e entre na hora, sem cadastro."
                : modo === "registro"
                  ? "Salve progresso, ranqueie e apareça no ranking global."
                  : "Use seu e-mail ou nick e a senha cadastrada."
            }}
          </p>
        </div>
        <BtnFecharDialog />
      </header>

      <nav
        v-if="passo === 'conta'"
        class="auth-abas"
        aria-label="Entrar ou cadastrar"
      >
        <button
          type="button"
          class="auth-aba"
          :class="{ ativa: modo === 'entrada' }"
          @click="modo = 'entrada'; limparErros()"
        >
          Entrar
        </button>
        <button
          type="button"
          class="auth-aba"
          :class="{ ativa: modo === 'registro' }"
          @click="modo = 'registro'; limparErros()"
        >
          Criar conta
        </button>
      </nav>

      <div class="auth-scroll">
        <template v-if="passo === 'visitante'">
          <section class="auth-visitante-topo">
            <label class="auth-campo">
              <span>Seu nome no jogo</span>
              <input
                v-model="nickVisitante"
                type="text"
                maxlength="20"
                class="auth-input"
                :class="{ 'auth-input-invalido': !!erroVisitante }"
                autocomplete="nickname"
                placeholder="ex: maria"
                :aria-invalid="!!erroVisitante"
                :aria-describedby="
                  erroVisitante
                    ? 'auth-erro-visitante'
                    : avisoNickCurto
                      ? 'auth-aviso-visitante'
                      : undefined
                "
                @input="normalizarNickVisitante"
              />
              <span class="auth-dica">
                3–20 caracteres (a–z, números ou _). Se já existir, você ganha Maria1, Maria2…
              </span>
              <p
                v-if="avisoNickCurto && !erroVisitante"
                id="auth-aviso-visitante"
                class="auth-aviso-campo"
              >
                {{ avisoNickCurto }}
              </p>
              <p
                v-if="erroVisitante"
                id="auth-erro-visitante"
                class="auth-erro-campo"
                role="alert"
              >
                {{ erroVisitante }}
              </p>
            </label>
            <button
              type="button"
              class="btn-modo btn-modo-destaque btn-largo"
              :disabled="enviando"
              @click="visitante"
            >
              Entrar como visitante
            </button>
          </section>

          <section class="auth-acesso-conta" aria-label="Conta com e-mail">
            <p class="auth-acesso-legenda">Já tem conta ou quer ranquear?</p>
            <button
              type="button"
              class="btn-modo btn-modo-conta-destaque btn-largo"
              @click="abrirPassoConta('entrada')"
            >
              Logar / Criar conta
            </button>
          </section>
        </template>

        <template v-else>
          <button
            v-if="!store.dialogContaForcarRegistro"
            type="button"
            class="auth-voltar"
            @click="voltarPassoVisitante"
          >
            ← Voltar
          </button>

          <form
            class="auth-form"
            @submit.prevent="modo === 'registro' ? registrar() : login()"
          >
            <p
              v-if="erroConta"
              class="auth-erro-campo auth-erro-form"
              role="alert"
            >
              {{ erroConta }}
            </p>

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
                @input="
                  nickForm = nickForm.toLowerCase().replace(/[^a-z0-9_]/g, '');
                  limparErros();
                "
              />
              <span class="auth-dica">3–20 caracteres: letras minúsculas, números ou _</span>
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
                @input="limparErros"
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
                @input="limparErros"
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
                @input="limparErros"
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
        </template>
      </div>
    </template>
  </dialog>
</template>
