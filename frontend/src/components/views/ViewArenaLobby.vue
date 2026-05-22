<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import JogadorLobbyItem from "../arena/JogadorLobbyItem.vue";
import QrCodigo from "../ui/QrCodigo.vue";

const store = useTermoStore();

const ocupacao = computed(() => {
  const max = store.dadosSala?.configuracao?.maximoJogadores || 4;
  const n = store.lobbyJogadores.length;
  return { n, max };
});

const contagemProntos = computed(() => {
  const prontos = store.dadosSala?.prontosOnline ?? 0;
  const total = store.dadosSala?.totalProntidao ?? 0;
  return { prontos, total };
});
</script>

<template>
  <section class="view view-ativa view-lobby">
    <article class="sala-espera">
      <header class="lobby-cabecalho">
        <div class="lobby-cabecalho-topo">
          <span class="lobby-codigo-mini">{{ store.codigoSala }}</span>
          <span
            v-if="store.badgeConexaoVisivel"
            class="badge-conexao"
            :class="store.wsConectado ? 'online' : 'offline'"
          >
            {{ store.wsConectado ? "Ao vivo" : "Reconectando" }}
          </span>
        </div>
        <h2 class="lobby-titulo">Sala de espera</h2>
        <p class="lobby-status-texto">{{ store.lobbyStatus }}</p>
      </header>

      <section class="lobby-convite" aria-label="Convite para a sala">
        <div class="lobby-convite-principal">
          <p class="lobby-convite-label">Código para entrar</p>
          <p class="lobby-codigo-grande" aria-label="Código da sala">
            {{ store.codigoSala }}
          </p>
          <div class="lobby-copiar-par">
            <button
              type="button"
              class="btn-lobby-copiar"
              @click="store.copiarTexto(store.codigoSala, 'Código copiado!')"
            >
              Copiar código
            </button>
            <button
              type="button"
              class="btn-lobby-copiar"
              @click="store.copiarTexto(store.linkSalaAtual, 'Link copiado!')"
            >
              Copiar link
            </button>
          </div>
        </div>
        <div class="lobby-convite-qr">
          <QrCodigo :texto="store.linkSalaAtual" :tamanho="128" rotulo="QR da sala" />
        </div>
      </section>

      <section v-if="store.lobbyChips.length" class="lobby-config" aria-label="Regras da sala">
        <ul class="lobby-config-lista">
          <li v-for="(chip, i) in store.lobbyChips" :key="i">{{ chip }}</li>
        </ul>
      </section>

      <section class="lobby-jogadores" aria-label="Jogadores na sala">
        <div class="lobby-jogadores-cabecalho">
          <h3>Jogadores</h3>
          <span class="lobby-contador-prontos">
            {{ contagemProntos.prontos }}/{{ contagemProntos.total }} prontos
            · {{ ocupacao.n }}/{{ ocupacao.max }}
          </span>
        </div>
        <ul class="lista-jogadores lobby-lista-jogadores">
          <JogadorLobbyItem
            v-for="j in store.lobbyJogadores"
            :key="j.idJogador || j.nomeJogador"
            :jogador="j"
            :criador-id="store.dadosSala?.criadorId"
            :sou-host="!!(store.dadosSala?.souCriador ?? store.souCriador)"
            @expulsar="store.expulsarJogadorLobby"
          />
        </ul>
      </section>

      <footer class="lobby-rodape">
        <button
          type="button"
          class="btn-modo btn-modo-sec btn-largo"
          :class="{ 'btn-pronto-ativo': store.euProntoLobby }"
          @click="store.alternarProntoLobby()"
        >
          {{ store.euProntoLobby ? "Pronto ✓" : "Marcar pronto" }}
        </button>

        <button
          v-if="store.dadosSala?.souCriador ?? store.souCriador"
          type="button"
          class="btn-modo btn-largo lobby-btn-iniciar"
          :disabled="!store.podeIniciarArena"
          @click="store.wsEnviar('iniciar')"
        >
          Iniciar partida
        </button>

        <p
          v-if="(store.dadosSala?.souCriador ?? store.souCriador) && !store.podeIniciarArena"
          class="lobby-rodape-dica"
        >
          {{ store.motivoNaoIniciarArena || "Aguarde todos marcarem pronto." }}
        </p>
        <p v-else-if="!(store.dadosSala?.souCriador ?? store.souCriador)" class="lobby-rodape-dica">
          Marque pronto e aguarde o host iniciar a partida.
        </p>

        <button
          type="button"
          class="btn-lobby-sair"
          @click="store.confirmarVoltarInicio()"
        >
          Sair da sala
        </button>
      </footer>
    </article>
  </section>
</template>
