<script setup>
import { onMounted, onUnmounted } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import { INTERVALO_SALAS_PUBLICAS_MS } from "../../utils/constantes.js";
import EstadoVazio from "../ui/EstadoVazio.vue";

const store = useTermoStore();
let timerSalas = null;

const filtros = [
  { id: "todas", rotulo: "Todas" },
  { id: "vaga", rotulo: "Com vaga" },
  { id: "pontos", rotulo: "Maratona" },
  { id: "vitorias", rotulo: "Vitórias" },
];

function entrarSala(codigo) {
  store.codigoEntrada = codigo;
  store.entrarSala();
}

onMounted(() => {
  store.conectarLobbyWs();
  timerSalas = setInterval(() => {
    if (store.view === "inicio" && !store.lobbyWsConectado) {
      store.carregarSalasPublicas();
    }
  }, INTERVALO_SALAS_PUBLICAS_MS);
});

onUnmounted(() => {
  if (timerSalas) clearInterval(timerSalas);
});
</script>

<template>
  <section class="painel-extras painel-salas-so">
    <div class="painel-card painel-salas-publicas">
      <div class="painel-salas-cabecalho">
        <h3>Salas públicas</h3>
        <span
          class="badge-ao-vivo"
          :class="{
            online: store.lobbyWsConectado,
            offline: store.lobbyWsReconectando,
          }"
          :title="
            store.lobbyWsConectado
              ? 'Lista em tempo real via WebSocket'
              : store.lobbyWsReconectando
                ? 'Reconectando ao servidor…'
                : 'Atualização periódica'
          "
        >
          {{
            store.lobbyWsConectado
              ? "Ao vivo"
              : store.lobbyWsReconectando
                ? "Reconectando…"
                : "Atualizando…"
          }}
        </span>
      </div>
      <div class="filtros-salas" role="tablist" aria-label="Filtrar salas">
        <button
          v-for="f in filtros"
          :key="f.id"
          type="button"
          class="chip-filtro"
          :class="{ ativo: store.filtroSalasPublicas === f.id }"
          @click="store.definirFiltroSalasPublicas(f.id)"
        >
          {{ f.rotulo }}
        </button>
      </div>
      <ul
        v-if="store.carregandoHome && !store.salasPublicas.length"
        class="lista-salas-publicas lista-loading"
      >
        <li v-for="n in 3" :key="n" class="skeleton-linha sala-publica-skeleton" />
      </ul>
      <ul v-else class="lista-salas-publicas">
        <EstadoVazio
          v-if="!store.salasPublicasFiltradas.length"
          icone="🎮"
          :titulo="store.salasPublicas.length ? 'Nenhuma sala neste filtro' : 'Nenhuma sala aberta'"
          texto="Crie uma sala pública na Arena."
        />
        <li
          v-for="s in store.salasPublicasFiltradas"
          :key="s.codigoSala"
          class="sala-publica-item"
          :class="{ 'sala-publica-item-vaga': s.temVaga }"
        >
          <div class="sala-publica-corpo">
            <div class="sala-publica-linha-topo">
              <span class="sala-codigo" aria-label="Código da sala">{{
                s.codigoSala
              }}</span>
              <span v-if="s.temVaga" class="badge-vaga">Vaga</span>
              <span v-else class="badge-sala-cheia">Cheia</span>
            </div>
            <p class="sala-publica-detalhe">
              <span class="sala-online">
                <span class="sala-online-ponto" aria-hidden="true" />
                {{ s.online }}/{{ s.jogadores || s.maximoJogadores }} online
              </span>
              <span class="sala-modo">{{ s.modoSessaoTexto }}</span>
            </p>
          </div>
          <button
            type="button"
            class="btn-sala-entrar"
            :disabled="!s.temVaga"
            @click="entrarSala(s.codigoSala)"
          >
            Entrar
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>
