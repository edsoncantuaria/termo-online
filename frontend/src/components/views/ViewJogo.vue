<script setup>
import { computed } from "vue";
import { useTermoStore } from "../../stores/termo.js";
import GradeTermo from "../jogo/GradeTermo.vue";
import GradesMulti from "../jogo/GradesMulti.vue";
import TecladoVirtual from "../jogo/TecladoVirtual.vue";
import TentativasDots from "../jogo/TentativasDots.vue";
import JogadorRodadaCard from "../arena/JogadorRodadaCard.vue";
import JogadorAvatar from "../jogo/JogadorAvatar.vue";

const store = useTermoStore();

function encerrarSessao() {
  store.mostrarConfirmacao({
    titulo: "Encerrar sessão?",
    mensagem: "A partida será encerrada para todos os jogadores.",
    dica: "Somente o host pode fazer isso.",
    textoConfirmar: "Encerrar",
    textoCancelar: "Cancelar",
    aoConfirmar: () => store.wsEnviar("encerrarSessao"),
  });
}

function confirmarDesistencia() {
  store.mostrarConfirmacao({
    titulo: "Desistir da partida?",
    mensagem:
      store.modoJogoRanqueada
        ? "Você perderá o duelo ranqueado e os pontos serão aplicados."
        : "Você sairá da partida em andamento.",
    textoConfirmar: "Desistir",
    textoCancelar: "Continuar jogando",
    aoConfirmar: () => store.desistirPartida(),
  });
}

const mostrarBotaoDesistir = computed(
  () =>
    store.modoJogoArena ||
    store.modoJogoRanqueada
);

const textoEntreRodadas = computed(() => {
  const D = store.dadosSala;
  if (!D?.placar?.length) return "Aguardando próxima rodada.";
  const lider = D.placar[0];
  const meta = store.metaVitoriasArena;
  if (store.porVitoriasArena) {
    return `${lider.nomeJogador} lidera com ${lider.vitoriasRodada || 0} de ${meta} vitórias.`;
  }
  return `${lider.nomeJogador} lidera com ${lider.pontosAcumulados} pontos.`;
});

const verOutros = computed(
  () => !!store.dadosSala?.configuracao?.verOutros
);

function avatarPlacar(j) {
  return j.idJogador === store.idJogador
    ? store.avatarIdEfetivo()
    : j.avatarId;
}
</script>

<template>
  <section class="view view-jogo view-ativa">
    <div
      v-if="store.countdownSegundos != null"
      class="overlay-countdown"
      aria-live="assertive"
    >
      <p class="countdown-legenda">Próxima rodada</p>
      <span class="countdown-numero">{{ store.countdownSegundos }}</span>
    </div>

    <div class="layout-jogo">
      <div class="jogo-principal">
        <div
          v-if="store.badgeEstadoJogo"
          class="faixa-estado"
          :class="`faixa-estado--${store.badgeEstadoJogo.tipo}`"
          role="status"
        >
          <span class="faixa-estado-ponto" aria-hidden="true" />
          <span>{{ store.badgeEstadoJogo.texto }}</span>
        </div>

        <div class="jogo-meta">
          <span class="modo-pill">{{ store.pillModoTexto }}</span>
          <div class="jogo-meta-direita">
            <span
              v-if="store.cronometroVisivel"
              class="timer-arena"
              :class="{ urgente: store.cronometroUrgente }"
            >
              <span class="timer-icone" aria-hidden="true">⏱</span>
              {{ store.cronometroTexto }}
            </span>
            <TentativasDots />
          </div>
        </div>

        <div
          class="grade-wrap"
          :class="{
            'grade-aguardando': store.carregandoChute,
            'grade-wrap--multi': store.mostrarGradesMulti,
          }"
        >
          <GradesMulti v-if="store.mostrarGradesMulti" />
          <GradeTermo
            v-if="store.mostrarGradePrincipal"
            :linhas="store.linhasGradePrincipal"
            :shake-linha="store.linhaShake"
            :editavel="store.podeEditarGradeAtual"
            @selecionar-celula="(_, col) => store.selecionarCelula(col)"
          />
        </div>

        <Transition name="toast-rodada">
          <p
            v-if="store.toastVitoriaRodada"
            class="vitoria-rodada-toast"
            aria-live="polite"
          >
            {{ store.toastVitoriaRodada }}
          </p>
        </Transition>

        <div
          v-if="
            store.dadosSala?.estadoSala === 'pausada' ||
            store.dadosSala?.pausada
          "
          class="card-aguardo card-pausa-partida"
          role="status"
        >
          <span class="card-aguardo-icone" aria-hidden="true">⏸</span>
          <p>
            {{
              store.dadosSala?.motivoPausa ||
              "Partida pausada — aguardando reconexão"
            }}
          </p>
          <p
            v-if="store.dadosSala?.segundosPausaRestantes != null"
            class="card-pausa-timer"
          >
            Tempo restante: {{ store.dadosSala.segundosPausaRestantes }}s
          </p>
        </div>

        <div
          v-if="store.mensagemAguardoArena"
          class="card-aguardo"
          role="status"
        >
          <span class="card-aguardo-icone" aria-hidden="true">⋯</span>
          <p>{{ store.mensagemAguardoArena }}</p>
        </div>

        <p v-if="store.mostrarDicaCelulas" class="dica-celulas">
          Clique numa casa vazia e monte a palavra em qualquer ordem
        </p>

        <button
          v-if="mostrarBotaoDesistir && !store.espectador && !store.dadosSala?.partidaEncerrada"
          type="button"
          class="btn-modo btn-modo-sec btn-desistir-partida"
          @click="confirmarDesistencia"
        >
          Desistir da partida
        </button>

        <TecladoVirtual v-if="!store.espectador" />
      </div>

      <aside v-if="store.lateralVisivel" class="jogo-lateral">
        <div
          v-if="store.palavraReveladaArena"
          class="palavra-revelada-bloco"
        >
          <span class="palavra-revelada-label">Palavra da rodada</span>
          <strong class="palavra-revelada-texto">{{
            store.palavraReveladaArena
          }}</strong>
        </div>

        <div v-if="store.modoJogoArena" class="placar-arena">
          <h3 class="lateral-titulo">Placar da sessão</h3>
          <p class="rodada-info">{{ store.rodadaInfoTexto }}</p>
          <ol class="lista-placar lista-placar-v2">
            <li
              v-for="j in store.placarArenaEnriquecido"
              :key="j.idJogador"
              class="placar-linha"
              :class="{
                campeao:
                  store.dadosSala?.partidaEncerrada && j.posicao === 1,
                'placar-lider': j.posicao === 1,
              }"
              :data-sou-eu="j.idJogador === store.idJogador ? '1' : undefined"
            >
              <span class="placar-pos">{{ j.posicao }}</span>
              <div class="placar-corpo">
                <div class="placar-linha-topo">
                  <span class="placar-jogador">
                    <JogadorAvatar
                      :nome="j.nomeJogador"
                      :avatar-id="avatarPlacar(j)"
                      pequeno
                    />
                    <span class="placar-nome">{{ j.nomeJogador }}</span>
                  </span>
                  <span class="placar-pontos">
                    <template v-if="store.porVitoriasArena">
                      <span class="placar-valor">{{
                        j.vitoriasRodada || 0
                      }}</span>
                      <span class="placar-unidade"
                        >/{{ store.metaVitoriasArena }} vit.</span
                      >
                    </template>
                    <template v-else>
                      <span class="placar-valor">{{
                        j.pontosAcumulados
                      }}</span>
                      <span class="placar-unidade">pts</span>
                      <span
                        v-if="
                          store.dadosSala?.estadoSala === 'entre_rodadas' &&
                          j.pontosUltimaRodada
                        "
                        class="pts-rodada"
                        >+{{ j.pontosUltimaRodada }}</span
                      >
                    </template>
                  </span>
                </div>
                <div
                  class="placar-barra"
                  role="presentation"
                  :style="{ '--prog': `${j.progresso}%` }"
                />
              </div>
            </li>
          </ol>
        </div>

        <div v-if="store.painelEntreRodadas" class="entre-rodadas entre-rodadas-v2">
          <div class="entre-rodadas-cabecalho">
            <span class="entre-rodadas-icone" aria-hidden="true">✓</span>
            <h3>Rodada encerrada</h3>
          </div>
          <p class="entre-rodadas-resumo">{{ textoEntreRodadas }}</p>
          <p
            v-if="store.dadosSala?.mensagemFimRodada"
            class="entre-rodadas-verdes"
            role="status"
          >
            {{ store.dadosSala.mensagemFimRodada }}
          </p>
          <p
            v-if="store.mensagemAguardoArena"
            class="entre-rodadas-aguardo"
          >
            {{ store.mensagemAguardoArena }}
          </p>
          <div class="entre-rodadas-acoes">
            <button
              v-if="store.dadosSala?.podeProximaRodada"
              type="button"
              class="btn-modo btn-largo btn-destaque"
              @click="store.wsEnviar('proximaRodada')"
            >
              Próxima rodada →
            </button>
            <button
              v-if="store.dadosSala?.podeEncerrarSessao"
              type="button"
              class="btn-modo btn-modo-sec btn-largo"
              @click="encerrarSessao"
            >
              Encerrar sessão
            </button>
          </div>
        </div>

        <div v-if="store.painelChatVisivel" class="chat-arena">
          <h3 class="lateral-titulo">Chat rápido</h3>
          <ul class="lista-chat" aria-live="polite">
            <li
              v-for="msg in store.chatMensagens"
              :key="msg.chave"
              class="chat-msg"
              :class="{ 'chat-msg-saindo': msg.saindo }"
            >
              <strong>{{ msg.nomeJogador }}</strong> {{ msg.texto }}
            </li>
          </ul>
          <div class="chat-botoes">
            <button
              v-for="frase in store.frasesChat"
              :key="frase"
              type="button"
              class="btn-chat-frase"
              @click="store.enviarChatFrase(frase)"
            >
              {{ frase }}
            </button>
          </div>
        </div>

        <h3 class="lateral-titulo titulo-outros">{{ store.tituloOutros }}</h3>
        <p v-if="store.modoJogoRanqueada" class="dica-outros-multi">
          Modo competitivo: você só vê se o oponente já chutou ou não.
        </p>
        <p
          v-else-if="store.outrosNaRodada.length >= 2 && verOutros"
          class="dica-outros-multi"
        >
          Resumo da melhor tentativa — toque para ver o tabuleiro completo.
        </p>
        <div
          class="outros-jogadores"
          :class="{
            'outros-jogadores--multi': store.outrosNaRodada.length >= 2,
          }"
        >
          <JogadorRodadaCard
            v-for="j in store.outrosNaRodada"
            :key="j.idJogador"
            :jogador="j"
            :ver-outros="verOutros"
            :modo-competitivo="store.modoJogoRanqueada"
            :modo-multiplo="store.outrosNaRodada.length >= 2"
            :max-tentativas="store.maxTentativas"
          />
        </div>
      </aside>
    </div>
  </section>
</template>
