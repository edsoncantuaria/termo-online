/** Ações Pinia: fila ranqueada, ranking e revanche. */
import { api } from "../../services/api.js";
import { SalvarAuthLocal } from "../../utils/auth.js";
import { LimparSessao } from "../../utils/sessao.js";
import { TocarSom } from "../../lib/som.js";

let timerFilaRanqueada = null;

export function pararFilaRanqueada() {
  if (timerFilaRanqueada) {
    clearInterval(timerFilaRanqueada);
    timerFilaRanqueada = null;
  }
  this.filaRanqueada = false;
  this.filaSegundos = null;
  this.filaFase = null;
  this.filaMensagem = "";
  this.filaJogadoresNaFila = 0;
  this.filaJogadoresOnline = 0;
  this.filaPreview = [];
  this.filaBusca = null;
  api.ranqueadaSairFila().catch(() => {});
}

export async function entrarFilaRanqueada() {
  if (!this.exigirContaRegistrada()) return;
  if (this.modo === "arena" && this.codigoSala) {
    this.mostrarToast("Saia da Arena antes de buscar ranqueado", true);
    return;
  }
  pararFilaRanqueada.call(this);
  this.filaRanqueada = true;
  try {
    const D = await api.ranqueadaEntrarFila();
    if (D.estado === "encontrado") {
      await entrarSalaRanqueada.call(this, D);
      return;
    }
    timerFilaRanqueada = setInterval(() => pollFilaRanqueada.call(this), 2000);
    await pollFilaRanqueada.call(this);
  } catch (e) {
    this.filaRanqueada = false;
    this.mostrarToast(e.message, true);
  }
}

export async function pollFilaRanqueada() {
  if (!this.filaRanqueada) return;
  try {
    const D = await api.ranqueadaStatusFila();
    if (D.estado === "aguardando") {
      this.filaSegundos = D.segundos ?? null;
      this.filaFase = D.fase ?? null;
      this.filaMensagem = D.mensagem ?? "";
      this.filaJogadoresNaFila = D.jogadoresNaFila ?? 0;
      this.filaJogadoresOnline = D.jogadoresOnline ?? D.jogadoresNaFila ?? 0;
      this.filaPreview = D.filaPreview ?? [];
      this.filaBusca = D.busca ?? null;
    }
    if (D.estado === "encontrado") {
      pararFilaRanqueada.call(this);
      this.fecharDialogs();
      await entrarSalaRanqueada.call(this, D);
    }
  } catch {
    /* ok */
  }
}

export async function entrarSalaRanqueada(D) {
  try {
    const R = await api.salaEstado(D.codigoSala, D.idJogador);
    if (!R.ok) throw new Error("Sala não encontrada");
    const estado = await R.json();
    entrarNaSalaRanqueada.call(this, estado);
    TocarSom("entrada");
    this.atualizarArena(estado);
  } catch (e) {
    this.mostrarToast(e.message || "Erro ao entrar no duelo", true);
  }
}

export function entrarNaSalaRanqueada(D) {
  LimparSessao();
  this.modo = "ranqueada";
  this.configArena = D.configuracao;
  this.codigoSala = D.codigoSala;
  this.idJogador = D.idJogador;
  this.souCriador = D.souCriador;
  this.codigoEntrada = "";
  this.dadosSala = D;
  this.fecharDialogs();
  if (D.estadoSala === "aguardando") {
    this.irParaView("inicio");
  }
  this.conectarWs();
  this.persistir();
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

export async function solicitarRevancheRanqueada() {
  if (!this.exigirContaRegistrada()) return;
  this.fecharDialogs();
  try {
    const D = await api.ranqueadaRevanche();
    if (D.fila?.estado === "encontrado") {
      await entrarSalaRanqueada.call(this, D.fila);
      return;
    }
    this.filaRanqueada = true;
    this.filaMensagem = D.mensagem || "Buscando revanche…";
    timerFilaRanqueada = setInterval(() => pollFilaRanqueada.call(this), 2000);
    await pollFilaRanqueada.call(this);
    this.mostrarToast(D.mensagem || "Revanche na fila", false, true);
  } catch (e) {
    this.mostrarToast(e.message, true);
  }
}

export const acoesRanqueada = {
  pararFilaRanqueada,
  entrarFilaRanqueada,
  pollFilaRanqueada,
  entrarSalaRanqueada,
  entrarNaSalaRanqueada,
  carregarRankingRanqueado,
  solicitarRevancheRanqueada,
};
