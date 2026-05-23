<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { useInstalarPwa } from "../../composables/useInstalarPwa.js";
import BtnFecharDialog from "../dialogs/BtnFecharDialog.vue";

const store = useTermoStore();

const estaNoMenuPrincipal = computed(
  () =>
    store.view === "inicio" &&
    !store.deveExibirTutorial &&
    !store.dialogAberto
);

const {
  podeMostrar,
  minimizada,
  dialogoAberto,
  ehAndroid,
  ehIosSafari,
  ehIosInApp,
  temPromptAndroid,
  textoPrincipal,
  rotuloBotao,
  minimizar,
  expandir,
  fecharDialogo,
  acaoPrincipal,
  copiarLinkSafari,
} = useInstalarPwa(estaNoMenuPrincipal);

function toast(texto, erro) {
  store.mostrarToast(texto, erro);
}

async function instalarAndroidNoDialogo() {
  await acaoPrincipal();
  fecharDialogo();
}
</script>

<template>
  <Teleport to="body">
    <button
      v-if="podeMostrar && minimizada"
      type="button"
      class="pwa-fab-instalar"
      aria-label="Instalar jogo no celular"
      @click="expandir"
    >
      <span class="pwa-fab-icone" aria-hidden="true">📲</span>
      Instalar jogo
    </button>

    <aside
      v-else-if="podeMostrar"
      class="pwa-faixa-instalar"
      role="region"
      aria-label="Instalar aplicativo"
    >
      <div class="pwa-faixa-corpo">
        <span class="pwa-faixa-icone" aria-hidden="true">📲</span>
        <p class="pwa-faixa-texto">{{ textoPrincipal }}</p>
        <div class="pwa-faixa-acoes">
          <button
            type="button"
            class="btn-modo btn-modo-destaque pwa-faixa-btn-principal"
            @click="acaoPrincipal"
          >
            {{ rotuloBotao }}
          </button>
          <button type="button" class="pwa-faixa-btn-sec" @click="minimizar">
            Agora não
          </button>
        </div>
      </div>
    </aside>

    <div
      v-if="dialogoAberto"
      class="pwa-dialog-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pwa-instalar-titulo"
      @click.self="fecharDialogo"
    >
      <div class="pwa-dialog-card" @click.stop>
        <header class="pwa-dialog-cabecalho">
          <h2 id="pwa-instalar-titulo">Instalar Termo no celular</h2>
          <BtnFecharDialog :ao-fechar="fecharDialogo" />
        </header>

        <div class="pwa-dialog-corpo">
          <template v-if="ehIosSafari">
            <ol class="pwa-passos">
              <li>
                Toque em <strong>Compartilhar</strong>
                <span class="pwa-passos-icone" aria-hidden="true">⎋</span>
                na barra inferior do Safari.
              </li>
              <li>
                Role e escolha <strong>Adicionar à Tela de Início</strong>.
              </li>
              <li>Toque em <strong>Adicionar</strong>.</li>
            </ol>
            <p class="pwa-dica">
              Depois, abra pelo ícone na tela inicial — tela cheia, como um app.
            </p>
          </template>

          <template v-else-if="ehIosInApp">
            <p class="pwa-dica">
              Este app (Chrome, Instagram, etc.) não instala PWAs. Use o
              <strong>Safari</strong>:
            </p>
            <ol class="pwa-passos">
              <li>Copie o link abaixo.</li>
              <li>Cole na barra do Safari e abra o site.</li>
              <li>Compartilhar → Adicionar à Tela de Início.</li>
            </ol>
            <button
              type="button"
              class="btn-modo btn-modo-destaque btn-largo"
              @click="copiarLinkSafari(toast)"
            >
              Copiar link do jogo
            </button>
          </template>

          <template v-else-if="ehAndroid">
            <p v-if="temPromptAndroid" class="pwa-dica">
              Toque em <strong>Instalar jogo</strong> — o Android mostra a
              confirmação nativa.
            </p>
            <ol v-else class="pwa-passos">
              <li>Menu <strong>⋮</strong> do Chrome (canto superior).</li>
              <li>
                <strong>Instalar app</strong> ou
                <strong>Adicionar à tela inicial</strong>.
              </li>
              <li>Confirme na gaveta de apps.</li>
            </ol>
            <button
              v-if="temPromptAndroid"
              type="button"
              class="btn-modo btn-modo-destaque btn-largo"
              @click="instalarAndroidNoDialogo"
            >
              Instalar jogo
            </button>
          </template>
        </div>

        <footer class="pwa-dialog-rodape">
          <button type="button" class="btn-modo btn-modo-sec btn-largo" @click="fecharDialogo">
            Fechar
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>
