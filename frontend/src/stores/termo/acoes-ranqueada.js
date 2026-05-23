/** Ações Pinia: fila ranqueada, ranking e revanche. */
import { api } from "../../services/api.js";
import { SalvarAuthLocal } from "../../utils/auth.js";
import { LimparSessao } from "../../utils/sessao.js";
import { TocarSom } from "../../lib/som.js";

let timerFilaRanqueada = null;
let timerEscapeConectandoFila = null;

const ESCAPE_CONECTANDO_FILA_MS = 12_000;

function PararPollFilaRanqueada() {
  if (timerFilaRanqueada) {
    clearInterval(timerFilaRanqueada);
    timerFilaRanqueada = null;
  }
}

function LimparEstadoFilaUi(store) {
  store.filaRanqueada = false;
  store.filaPodeCancelar = true;
  store.filaSegundos = null;
  store.filaFase = null;
  store.filaMensagem = "";
  store.filaJogadoresNaFila = 0;
  store.filaJogadoresOnline = null;
  store.filaPreview = [];
  store.filaBusca = null;
}

function PararTimerEscapeConectandoFila() {
  if (timerEscapeConectandoFila) {
    clearTimeout(timerEscapeConectandoFila);
    timerEscapeConectandoFila = null;
  }
}

export function pararFilaRanqueada(opcoes = {}) {
  const Forcar = opcoes?.forcar === true;
  if (
    !Forcar &&
    (this.filaFase === "conectando" || !this.filaPodeCancelar)
  ) {
    return;
  }
  PararTimerEscapeConectandoFila();
  PararPollFilaRanqueada();
  LimparEstadoFilaUi(this);
  api.ranqueadaSairFila().catch(() => {});
}

async function ProcessarMatchRanqueadoEncontrado(D) {
  PararPollFilaRanqueada();
  PararTimerEscapeConectandoFila();
  this.filaRanqueada = true;
  this.filaPodeCancelar = false;
  this.filaFase = "conectando";
  this.filaMensagem =
    D.nickOponente ? `Duelo com ${D.nickOponente}` : "Preparando o duelo…";
  this.filaPreview = [];
  timerEscapeConectandoFila = setTimeout(() => {
    timerEscapeConectandoFila = null;
    if (this.filaFase !== "conectando") return;
    this.filaPodeCancelar = true;
    this.filaMensagem =
      "Demorou para entrar — você pode cancelar e buscar de novo.";
    this.mostrarToast(this.filaMensagem, true);
  }, ESCAPE_CONECTANDO_FILA_MS);
  await new Promise((r) => setTimeout(r, 720));
  try {
    await entrarSalaRanqueada.call(this, D);
  } catch (e) {
    this.mostrarToast(
      e?.message || "Não foi possível entrar no duelo ranqueado.",
      true
    );
    api.ranqueadaSairFila().catch(() => {});
  } finally {
    PararTimerEscapeConectandoFila();
    LimparEstadoFilaUi(this);
  }
}

export async function entrarFilaRanqueada(treino = false) {
  if (!this.exigirContaRegistrada()) return;
  if (!(await this.assegurarSemConflitoJogoAtivo())) return;
  if (this.modo === "arena" && this.codigoSala) {
    this.mostrarToast("Saia da Arena antes de buscar ranqueado", true);
    return;
  }
  pararFilaRanqueada.call(this);
  this.filaRanqueada = true;
  this.filaPodeCancelar = true;
  this.filaUltimoContagemNaFila = 0;
  try {
    const D = await api.ranqueadaEntrarFila(!!treino);
    if (D.estado === "encontrado") {
      await ProcessarMatchRanqueadoEncontrado.call(this, D);
      return;
    }
    timerFilaRanqueada = setInterval(() => pollFilaRanqueada.call(this), 1000);
    await pollFilaRanqueada.call(this);
  } catch (e) {
    this.filaRanqueada = false;
    this.mostrarToast(e.message, true);
  }
}

export async function pollFilaRanqueada() {
  if (!this.filaRanqueada) return;
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    if (!this._filaAvisoOffline) {
      this._filaAvisoOffline = true;
      this.mostrarToast(
        "Sem conexão — a fila pausou até a internet voltar.",
        true,
        true
      );
    }
    return;
  }
  this._filaAvisoOffline = false;
  try {
    const D = await api.ranqueadaStatusFila();
    if (D.estado === "fila_cheia") {
      pararFilaRanqueada.call(this);
      this.mostrarToast(D.mensagem || "Fila cheia — tente em instantes", true);
      return;
    }
    if (D.estado === "idle") {
      pararFilaRanqueada.call(this);
      this.mostrarToast(
        "Você saiu da fila. Toque em Ranqueado para buscar de novo.",
        true
      );
      return;
    }
    if (D.estado === "aguardando") {
      const NaFila = D.jogadoresNaFila ?? 0;
      if (
        NaFila > this.filaUltimoContagemNaFila &&
        this.filaUltimoContagemNaFila > 0
      ) {
        this.mostrarToast(
          `${NaFila} jogador${NaFila === 1 ? "" : "es"} na fila agora`,
          false,
          true
        );
      }
      this.filaUltimoContagemNaFila = NaFila;
      this.filaSegundos = D.segundos ?? null;
      this.filaFase = D.fase ?? null;
      this.filaMensagem = D.mensagem ?? "";
      this.filaJogadoresNaFila = NaFila;
      this.filaJogadoresOnline =
        D.jogadoresOnline != null ? D.jogadoresOnline : null;
      this.filaPreview = D.filaPreview ?? [];
      this.filaBusca = D.busca ?? null;
    }
    if (D.estado === "encontrado") {
      this.mostrarToast(
        D.nickOponente
          ? `Duelo encontrado: ${D.nickOponente}`
          : "Oponente encontrado!",
        false,
        true
      );
      TocarSom("entrada");
      await ProcessarMatchRanqueadoEncontrado.call(this, D);
    }
  } catch (e) {
    const Seg = this.filaSegundos ?? 0;
    if (Seg >= 12) {
      this.mostrarToast(
        e?.message || "Falha ao atualizar a fila — verifique a conexão",
        true
      );
    }
  }
}

export async function entrarSalaRanqueada(D) {
  try {
    let estado;
    if (D.idPartida && D.tokenSessao) {
      estado = await api.partidaRetomar(
        D.idPartida,
        D.tokenSessao,
        D.idJogador
      );
    } else {
      estado = await api.salaEstado(D.codigoSala, D.idJogador);
    }
    entrarNaSalaRanqueada.call(this, estado, D);
    TocarSom("entrada");
  } catch (e) {
    this.mostrarToast(e.message || "Erro ao entrar no duelo", true);
  }
}

export function entrarNaSalaRanqueada(D, Credenciais = null, Opcoes = {}) {
  const encerrada = !!D.partidaEncerrada;
  LimparSessao();
  this.modo = "ranqueada";
  this.configArena = D.configuracao;
  this.codigoSala = D.codigoSala;
  this.idJogador = D.idJogador || Credenciais?.idJogador;
  this.aplicarCredenciaisPartida(Credenciais || D);
  this.souCriador = D.souCriador;
  this.codigoEntrada = "";
  this.dadosSala = D;
  this.fecharDialogs();
  if (encerrada && Opcoes.irParaInicioSeEncerrada !== false) {
    this.fecharSocketSala();
    this.irParaView("inicio");
    this.atualizarArena(D, { exibirResultadoEncerrada: Opcoes.exibirResultadoEncerrada });
    return;
  }
  this.conectarWs();
  this.iniciarTelaJogo("Ranqueado");
  this.atualizarArena(D, { exibirResultadoEncerrada: Opcoes.exibirResultadoEncerrada });
  this.persistir();
}

export async function carregarHistoricoRanqueado() {
  if (!this.conta?.podeRanqueada) {
    this.historicoRanqueado = [];
    return;
  }
  try {
    const D = await api.ranqueadaHistorico(20);
    this.historicoRanqueado = D.historico || [];
  } catch {
    this.historicoRanqueado = [];
  }
}

export async function carregarTemporadaRanqueada() {
  if (!this.conta?.podeRanqueada) {
    this.temporadaRanqueada = null;
    return;
  }
  try {
    this.temporadaRanqueada = await api.ranqueadaTemporada();
  } catch {
    this.temporadaRanqueada = null;
  }
}

export async function carregarRankingRanqueado() {
  if (!this.conta?.podeRanqueada) {
    this.rankingRanqueado = [];
    return;
  }
  try {
    const D = await api.ranqueadaRanking();
    this.rankingRanqueado = D.ranking || [];
    this.minhaPosicaoRanqueada = D.minhaPosicao ?? null;
    this.totalRanqueados = D.totalRanqueados ?? 0;
    if (D.eu) this.conta = D.eu;
  } catch {
    this.rankingRanqueado = [];
  }
}

/** Retoma fila ou duelo após recarregar o app (evita fila fantasma no servidor). */
export async function sincronizarFilaRanqueadaInicial() {
  if (!this.conta?.podeRanqueada) return false;
  if (this.jogoAtivo?.ativo && !this.jogoAtivo?.partidaEncerrada) {
    return false;
  }
  try {
    const D = await api.ranqueadaStatusFila();
    if (D.estado === "encontrado") {
      this.mostrarToast(
        D.nickOponente
          ? `Duelo encontrado: ${D.nickOponente}`
          : "Entrando no duelo ranqueado…",
        false
      );
      await ProcessarMatchRanqueadoEncontrado.call(this, D);
      return true;
    }
    if (D.estado === "aguardando") {
      this.filaRanqueada = true;
      this.filaPodeCancelar = true;
      this.filaMensagem = D.mensagem || "Busca ranqueada em andamento…";
      this.dialogAberto = "jogar";
      timerFilaRanqueada = setInterval(() => pollFilaRanqueada.call(this), 1000);
      await pollFilaRanqueada.call(this);
      this.mostrarToast("Busca ranqueada retomada — aguardando oponente.", false);
      return true;
    }
    if (D.estado === "idle" || D.estado === "fila_cheia") {
      PararPollFilaRanqueada();
      LimparEstadoFilaUi(this);
    }
  } catch {
    /* offline ou API indisponível */
  }
  return false;
}

export async function solicitarRevancheRanqueada() {
  if (!this.exigirContaRegistrada()) return;
  this.fecharDialogs();
  try {
    const D = await api.ranqueadaRevanche();
    if (D.fila?.estado === "encontrado") {
      await ProcessarMatchRanqueadoEncontrado.call(this, D.fila);
      return;
    }
    this.filaRanqueada = true;
    this.filaPodeCancelar = true;
    this.filaMensagem = D.mensagem || "Buscando revanche…";
    timerFilaRanqueada = setInterval(() => pollFilaRanqueada.call(this), 1000);
    await pollFilaRanqueada.call(this);
    this.mostrarToast(D.mensagem || "Revanche na fila", false, true);
  } catch (e) {
    this.mostrarToast(e.message, true);
  }
}

export const acoesRanqueada = {
  pararFilaRanqueada,
  sincronizarFilaRanqueadaInicial,
  entrarFilaRanqueada,
  pollFilaRanqueada,
  entrarSalaRanqueada,
  entrarNaSalaRanqueada,
  carregarRankingRanqueado,
  carregarHistoricoRanqueado,
  carregarTemporadaRanqueada,
  solicitarRevancheRanqueada,
};
