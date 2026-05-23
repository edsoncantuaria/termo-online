/** Jogo ativo na home: reconectar, abandonar, contagem e bloqueio de novo modo. */
import { api } from "../../services/api.js";
import { EhJogoAtivoOnline, EhModoSalaOnline } from "../../utils/modos.js";
import {
  DecrementarContagens,
  TextoBloqueioNovoModo,
  TextoContagemHero,
} from "../../utils/contagem-jogo-ativo.js";
import {
  JogoAtivoDeSessaoLocal,
  MesclarJogoAtivoComRetomar,
} from "../../utils/jogo-ativo.js";
import { ObterSessao, LimparSessao, PersistirSessao } from "../../utils/sessao.js";
import { DiariaJaJogadaLocal } from "../../utils/stats.js";
import { PartidaOnlineEmAndamento } from "../../utils/jogo.js";
import { entrarNaSalaRanqueada } from "./acoes-ranqueada.js";

let intervaloJogoAtivoHome = null;
let tickJogoAtivoHome = 0;

function PararTickJogoAtivoHome() {
  if (intervaloJogoAtivoHome) {
    clearInterval(intervaloJogoAtivoHome);
    intervaloJogoAtivoHome = null;
  }
}

function AplicarTickContagem(store) {
  const J = store.jogoAtivo;
  if (!EhJogoAtivoOnline(J)) {
    PararTickJogoAtivoHome();
    return;
  }
  const { pausa, abandono } = DecrementarContagens(J);
  const Atualizado = {
    ...J,
    segundosPausaRestantes:
      pausa ?? J.segundosPausaRestantes,
    segundosAteAbandono:
      abandono ?? J.segundosAteAbandono,
  };
  Atualizado.textoEstado = TextoContagemHero(Atualizado, {
    pausaRestante: Atualizado.segundosPausaRestantes,
    abandonoRestante: Atualizado.segundosAteAbandono,
  });
  store.jogoAtivo = Atualizado;
  if (
    (pausa === 0 || abandono === 0) &&
    tickJogoAtivoHome % 5 === 0
  ) {
    carregarJogoAtivo.call(store);
  }
}

export function IniciarTickJogoAtivoHome() {
  PararTickJogoAtivoHome();
  const store = this;
  if (
    !EhJogoAtivoOnline(store.jogoAtivo) ||
    store.view !== "inicio"
  ) {
    return;
  }
  tickJogoAtivoHome = 0;
  intervaloJogoAtivoHome = setInterval(() => {
    tickJogoAtivoHome += 1;
    if (store.view !== "inicio") {
      PararTickJogoAtivoHome();
      return;
    }
    AplicarTickContagem(store);
    if (tickJogoAtivoHome % 12 === 0) {
      carregarJogoAtivo.call(store);
    }
  }, 1000);
}

async function sincronizarJogoAtivoLocalComApi(Local) {
  if (!Local?.ativo || !EhJogoAtivoOnline(Local)) return Local;
  if (!Local.idPartida || !Local.tokenSessao) return Local;
  try {
    const Dados = await api.partidaRetomar(
      Local.idPartida,
      Local.tokenSessao,
      Local.idJogador
    );
    return MesclarJogoAtivoComRetomar(Local, Dados);
  } catch {
    return Local;
  }
}

export async function carregarJogoAtivo() {
  if (this.conta?.idConta && !this.conta?.ehVisitante) {
    try {
      const D = await api.contaJogoAtivo();
      if (D?.ativo) {
        if (EhJogoAtivoOnline(D)) {
          D.textoEstado = TextoContagemHero(D, {
            pausaRestante: D.segundosPausaRestantes,
            abandonoRestante: D.segundosAteAbandono,
          });
        }
        this.jogoAtivo = D;
      } else {
        let Local = JogoAtivoDeSessaoLocal(ObterSessao());
        if (Local) Local = await sincronizarJogoAtivoLocalComApi(Local);
        this.jogoAtivo = Local;
      }
    } catch {
      let Local = JogoAtivoDeSessaoLocal(ObterSessao());
      if (Local) Local = await sincronizarJogoAtivoLocalComApi(Local);
      this.jogoAtivo = Local;
    }
  } else {
    let Local = JogoAtivoDeSessaoLocal(ObterSessao());
    if (Local) Local = await sincronizarJogoAtivoLocalComApi(Local);
    if (Local && EhJogoAtivoOnline(Local)) {
      Local.textoEstado = TextoContagemHero(Local, {
        pausaRestante: Local.segundosPausaRestantes,
        abandonoRestante: Local.segundosAteAbandono,
      });
    }
    this.jogoAtivo = Local;
  }
  if (this.view === "inicio" && EhJogoAtivoOnline(this.jogoAtivo)) {
    IniciarTickJogoAtivoHome.call(this);
  } else {
    PararTickJogoAtivoHome();
  }
}

async function liberarJogoAtivoSoloSilencioso(store) {
  const J = store.jogoAtivo;
  if (J?.tipo !== "solo") return;
  LimparSessao();
  store.jogoAtivo = null;
  if (store.idPartida && !EhModoSalaOnline(store.modo)) {
    store.modo = null;
    store.idPartida = null;
    store.tokenPartida = null;
  }
  if (store.conta?.idConta && !store.conta?.ehVisitante) {
    await api.contaLimparJogoAtivo().catch(() => {});
  }
  PararTickJogoAtivoHome();
}

/**
 * Impede iniciar outro modo enquanto há partida arena/ranqueada pendente.
 * Partidas solo são descartadas silenciosamente ao iniciar outro modo.
 * @returns {Promise<boolean>} true se pode seguir
 */
export async function assegurarSemConflitoJogoAtivo() {
  await carregarJogoAtivo.call(this);
  const J = this.jogoAtivo;
  if (!J?.ativo) return true;
  if (this.view === "jogo" && EhModoSalaOnline(this.modo)) return true;

  if (!EhJogoAtivoOnline(J)) {
    await liberarJogoAtivoSoloSilencioso(this);
    return true;
  }

  const Mensagem = TextoBloqueioNovoModo(J, {
    pausaRestante: J.segundosPausaRestantes,
    abandonoRestante: J.segundosAteAbandono,
  });

  return new Promise((resolve) => {
    this.mostrarConfirmacao({
      titulo: `${J.titulo} pendente`,
      mensagem: Mensagem,
      dica: "Reconecte para continuar ou abandone para liberar outros modos.",
      textoConfirmar: "Reconectar",
      textoCancelar: "Abandonar partida",
      aoConfirmar: async () => {
        await reconectarJogoAtivo.call(this);
        resolve(false);
      },
      aoCancelar: () => {
        abandonarJogoAtivo.call(this);
        resolve(false);
      },
    });
  });
}

export async function reconectarJogoAtivo() {
  const J = this.jogoAtivo;
  if (!J?.ativo || this.carregandoJogoAtivo) return;

  this.carregandoJogoAtivo = true;
  try {
    if (J.tipo === "ranqueada" || J.tipo === "arena") {
      let estado;
      if (J.idPartida && (J.tokenSessao || this.conta?.idConta)) {
        estado = await api.partidaRetomar(
          J.idPartida,
          J.tokenSessao,
          J.idJogador
        );
      } else {
        const R = await api.salaEstado(J.codigoSala, J.idJogador);
        if (!R.ok) throw new Error("Não foi possível retomar a sala.");
        estado = await R.json();
      }
      if (J.tipo === "ranqueada") {
        if (estado.partidaEncerrada || estado.somenteResultado) {
          entrarNaSalaRanqueada.call(this, estado, J, {
            exibirResultadoEncerrada: true,
          });
          await this.carregarRankingRanqueado().catch(() => {});
          await this.carregarHistoricoRanqueado().catch(() => {});
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            await api.contaLimparJogoAtivo().catch(() => {});
          }
          LimparSessao();
        } else if (estado.podeRetomar === false) {
          const msg = estado.voceGanhou
            ? "Partida já encerrada — você venceu."
            : estado.vocePerdeu
              ? "Partida já encerrada — você perdeu."
              : "Partida já encerrada.";
          this.mostrarToast(msg, !estado.voceGanhou);
          LimparSessao();
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            await api.contaLimparJogoAtivo().catch(() => {});
          }
        } else if (PartidaOnlineEmAndamento(estado)) {
          entrarNaSalaRanqueada.call(this, estado, J, {
            exibirResultadoEncerrada: false,
          });
          this.mostrarDialogoRetomadaRanqueada(estado);
        } else {
          entrarNaSalaRanqueada.call(this, estado, J);
        }
      } else if (J.tipo === "arena") {
        if (estado.partidaEncerrada || estado.somenteResultado) {
          this.entrarNaSala(estado);
          this.conectarWs();
          this.irParaView("arenaLobby");
          this.atualizarArena(estado, { exibirResultadoEncerrada: true });
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            await api.contaLimparJogoAtivo().catch(() => {});
          }
          LimparSessao();
        } else if (estado.podeRetomar === false) {
          this.mostrarToast(
            estado.voceGanhou
              ? "Partida já encerrada — você venceu."
              : estado.vocePerdeu
                ? "Partida já encerrada — você perdeu."
                : "Partida já encerrada.",
            !estado.voceGanhou
          );
          LimparSessao();
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            await api.contaLimparJogoAtivo().catch(() => {});
          }
        } else {
          this.entrarNaSala(estado);
          if (estado.partidaEncerrada) {
            this.conectarWs();
            this.irParaView("arenaLobby");
          }
          this.atualizarArena(estado);
        }
      } else {
        this.entrarNaSala(estado);
        this.atualizarArena(estado);
      }
    } else if (J.tipo === "solo") {
      if (J.modoSolo === "diaria" && DiariaJaJogadaLocal()) {
        throw new Error("Palavra do dia já concluída neste aparelho.");
      }
      const D = await api.jogarEstado(J.idPartida, J.tokenPartida);
      if (D.encerrada) throw new Error("Partida já encerrada.");
      this.modo = D.modo;
      this.idPartida = D.idPartida;
      this.tokenPartida = D.tokenPartida || J.tokenPartida;
      this.dataDia = D.dataDia;
      const labels = {
        diaria: "Palavra do dia",
        pratica: "Prática",
        dueto: "Dueto",
        quarteto: "Quarteto",
        desafio: "Desafio",
      };
      this.iniciarTelaJogo(labels[D.modo] || D.modo);
      const salvo = ObterSessao();
      this.restaurarPartidaSolo(D, salvo?.solo);
      this.persistir();
    }
    PararTickJogoAtivoHome();
    this.jogoAtivo = null;
    this.fecharDialogs();
  } catch (e) {
    this.mostrarToast(e.message || "Não foi possível reconectar", true);
    await carregarJogoAtivo.call(this);
  } finally {
    this.carregandoJogoAtivo = false;
  }
}

export async function abandonarJogoAtivo() {
  const J = this.jogoAtivo;
  if (!J?.ativo) return;

  this.mostrarConfirmacao({
    titulo: "Abandonar partida?",
    mensagem:
      J.semPenalidade
        ? "Você voltará ao início. Como ainda não pontuou, nada será registrado no histórico nem em XP."
        : J.tipo === "ranqueada"
          ? J.penalidadeAbandonoRp && !J.semPenalidade
            ? `Você perderá o duelo e cerca de ${J.penalidadeAbandonoRp} pontos de RP (${J.pontosRanqueadaAtual ?? "?"} → ${J.pontosAposAbandonoEstimado ?? "?"}).`
            : "Você perderá o duelo ranqueado e os pontos serão aplicados."
          : J.tipo === "arena"
            ? "Você será removido da sala e não poderá voltar a esta partida."
            : "O progresso desta partida solo será perdido.",
    textoConfirmar: "Abandonar",
    textoCancelar: "Cancelar",
    aoConfirmar: async () => {
      this.carregandoJogoAtivo = true;
      try {
        if (J.tipo === "solo") {
          LimparSessao();
          this.modo = null;
          this.idPartida = null;
          this.tokenPartida = null;
          this.jogoAtivo = null;
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            await api.contaLimparJogoAtivo().catch(() => {});
          }
          this.mostrarToast("Partida abandonada.");
        } else {
          this.modo = J.tipo === "ranqueada" ? "ranqueada" : "arena";
          this.codigoSala = J.codigoSala;
          this.idJogador = J.idJogador;
          this.idPartida = J.idPartida;
          this.tokenSessao = J.tokenSessao;
          await this.desistirPartida();
          this.jogoAtivo = null;
        }
        PararTickJogoAtivoHome();
        await carregarJogoAtivo.call(this);
      } finally {
        this.carregandoJogoAtivo = false;
      }
    },
  });
}

/**
 * Após esgotar tentativas de WebSocket: consulta o servidor (partida pode ter acabado).
 */
export async function aoReconexaoWsEsgotada(store) {
  store.bannerReconexao = false;
  store.fecharSocketSala();
  const { idPartida, idJogador, tokenSessao, modo } = store;
  if (!idPartida || !idJogador || !EhModoSalaOnline(modo)) {
    store.mostrarToast("Conexão perdida. Voltando ao início.", true);
    await voltarInicioPreservandoPartida.call(store);
    return;
  }
  try {
    const estado = await api.partidaRetomar(
      idPartida,
      tokenSessao,
      idJogador
    );
    const cred = {
      codigoSala: estado.codigoSala || store.codigoSala,
      idJogador,
      idPartida,
      tokenSessao,
    };
    if (estado.partidaEncerrada || estado.somenteResultado) {
      if (modo === "ranqueada") {
        entrarNaSalaRanqueada.call(store, estado, cred, {
          exibirResultadoEncerrada: true,
        });
        await store.carregarRankingRanqueado().catch(() => {});
        await store.carregarHistoricoRanqueado().catch(() => {});
      } else {
        store.entrarNaSala(estado);
        store.atualizarArena(estado, { exibirResultadoEncerrada: true });
        store.irParaView("arenaLobby");
      }
      if (store.conta?.idConta && !store.conta?.ehVisitante) {
        await api.contaLimparJogoAtivo().catch(() => {});
      }
      LimparSessao();
      store.jogoAtivo = null;
      PararTickJogoAtivoHome();
      return;
    }
    if (PartidaOnlineEmAndamento(estado)) {
      if (modo === "ranqueada") {
        entrarNaSalaRanqueada.call(store, estado, cred, {
          exibirResultadoEncerrada: false,
        });
        store.mostrarDialogoRetomadaRanqueada(estado);
      } else {
        store.entrarNaSala(estado);
        store.atualizarArena(estado);
        store.conectarWs();
      }
      store.mostrarToast("Conexão restabelecida.", false);
      return;
    }
    const msg = estado.voceGanhou
      ? "Partida encerrada — você venceu."
      : estado.vocePerdeu
        ? "Partida encerrada — você perdeu."
        : "Partida encerrada.";
    store.mostrarToast(msg, !estado.voceGanhou);
    LimparSessao();
    await voltarInicioPreservandoPartida.call(store);
  } catch {
    store.mostrarToast("Conexão perdida. Voltando ao início.", true);
    await voltarInicioPreservandoPartida.call(store);
  }
}

export async function voltarInicioPreservandoPartida() {
  this.pararFilaRanqueada();
  this.pararCronometro();
  this.limparChat();
  this.fecharDialogs();

  if (EhModoSalaOnline(this.modo) && this.codigoSala && this.idJogador) {
    PersistirSessao(this.$state);
    this.fecharSocketSala();
  } else if (this.idPartida && this.modo) {
    PersistirSessao(this.$state);
  }

  this.modo = null;
  this.codigoSala = null;
  this.idJogador = null;
  this.dadosSala = null;
  this.configArena = null;
  this.estadoSalaArena = null;
  this.encerrada = false;
  this.bannerReconexao = false;
  this.souCriador = false;
  this.espectador = false;

  this.irParaView("inicio");
  await carregarJogoAtivo.call(this);
}

export const acoesJogoAtivo = {
  carregarJogoAtivo,
  assegurarSemConflitoJogoAtivo,
  reconectarJogoAtivo,
  abandonarJogoAtivo,
  aoReconexaoWsEsgotada,
  voltarInicioPreservandoPartida,
  IniciarTickJogoAtivoHome,
};
