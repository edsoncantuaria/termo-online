<script setup>
import { useTermoStore } from "../../stores/termo.js";
import { useInstalarPwa } from "../../composables/useInstalarPwa.js";

const store = useTermoStore();
const P = useInstalarPwa();

function toast(texto, erro) {
  store.mostrarToast(texto, erro);
}
</script>

<template>
  <Teleport to="body">
    <button
      v-if="P.podeMostrar && P.minimizada"
      type="button"
      class="pwa-fab-instalar"
      aria-label="Instalar jogo no celular"
      @click="P.expandir()"
    >
      <span class="pwa-fab-icone" aria-hidden="true">📲</span>
      Instalar jogo
    </button>

    <aside
      v-else-if="P.podeMostrar"
      class="pwa-faixa-instalar"
      role="region"
      aria-label="Instalar aplicativo"
    >
      <div class="pwa-faixa-corpo">
        <span class="pwa-faixa-icone" aria-hidden="true">📲</span>
        <p class="pwa-faixa-texto">{{ P.textoPrincipal }}</p>
        <div class="pwa-faixa-acoes">
          <button
            type="button"
            class="btn-modo btn-modo-destaque pwa-faixa-btn-principal"
            @click="P.acaoPrincipal()"
          >
            {{ P.rotuloBotao }}
          </button>
          <button
            type="button"
            class="pwa-faixa-btn-sec"
            @click="P.minimizar()"
          >
            Agora não
          </button>
        </div>
      </div>
    </aside>

    <div
      v-if="P.dialogoAberto"
      class="pwa-dialog-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pwa-instalar-titulo"
      @click.self="P.fecharDialogo()"
    >
      <div class="pwa-dialog-card">
        <header class="pwa-dialog-cabecalho">
          <h2 id="pwa-instalar-titulo">Instalar Termo no celular</h2>
          <button
            type="button"
            class="btn-fechar-dialog"
            aria-label="Fechar"
            @click="P.fecharDialogo()"
          >
            ×
          </button>
        </header>

        <div class="pwa-dialog-corpo">
          <template v-if="P.ehIosSafari">
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

          <template v-else-if="P.ehIosInApp">
            <p class="pwa-dica">
              Abra esta página no <strong>Safari</strong> (navegador do iPhone):
            </p>
            <ol class="pwa-passos">
              <li>Copie o link abaixo.</li>
              <li>Cole na barra do Safari e abra o site.</li>
              <li>Compartilhar → Adicionar à Tela de Início.</li>
            </ol>
            <button
              type="button"
              class="btn-modo btn-modo-destaque btn-largo"
              @click="P.copiarLinkSafari(toast)"
            >
              Copiar link do jogo
            </button>
          </template>

          <template v-else-if="P.ehAndroid">
            <p v-if="P.temPromptAndroid" class="pwa-dica">
              O Android vai pedir confirmação para instalar o app.
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
              v-if="P.temPromptAndroid"
              type="button"
              class="btn-modo btn-modo-destaque btn-largo"
              @click="P.acaoPrincipal(); P.fecharDialogo()"
            >
              Instalar jogo
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>
