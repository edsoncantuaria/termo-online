/** WebSocket e sync HTTP da arena / ranqueada. */
import { UrlWebSocket } from "../../config/origem.js";
import { api } from "../../services/api.js";
import { TocarSom } from "../../lib/som.js";
import { EhModoSalaOnline } from "../../utils/modos.js";
import { aoReconexaoWsEsgotada } from "./acoes-jogo-ativo.js";

let socketSala = null;
let intervaloSyncArena = null;
let intervaloPingArena = null;

export function obterSocketSala() {
  return socketSala;
}

export function fecharSocketSala() {
  if (!socketSala) return;
  socketSala.onclose = null;
  socketSala.onerror = null;
  socketSala.onmessage = null;
  try {
    if (socketSala.readyState === WebSocket.OPEN) {
      socketSala.send(JSON.stringify({ tipo: "sair", dados: {} }));
    }
  } catch {
    /* ok */
  }
  try {
    socketSala.close();
  } catch {
    /* ok */
  }
  socketSala = null;
}

export function pararSyncArena() {
  if (intervaloSyncArena) {
    clearInterval(intervaloSyncArena);
    intervaloSyncArena = null;
  }
  pararPingArena();
}

export function pararPingArena() {
  if (intervaloPingArena) {
    clearInterval(intervaloPingArena);
    intervaloPingArena = null;
  }
}

/** Mantém UltimaAtividade no lobby (evita expulsão aos 2 min). */
export function iniciarPingArena(store) {
  pararPingArena();
  if (!store.codigoSala || store.modo !== "arena") return;
  intervaloPingArena = setInterval(() => {
    if (
      store.view === "arenaLobby" &&
      store.dadosSala?.estadoSala === "aguardando" &&
      !store.dadosSala?.partidaEncerrada
    ) {
      wsEnviar("ativo");
    }
  }, 45_000);
}

export function wsEnviar(tipo, dados = {}) {
  if (socketSala?.readyState === WebSocket.OPEN) {
    socketSala.send(JSON.stringify({ tipo, dados }));
  }
}

export function processarWsArena(store, M) {
  if (M.tipo === "chuteInvalido") {
    store.carregandoChute = false;
    store.tratarChuteInvalido(M.mensagem);
  } else if (M.tipo === "erro") {
    store.carregandoChute = false;
    store.mostrarToast(M.mensagem, true);
    TocarSom("erro");
    store.linhaShake = store.tentativa;
    setTimeout(() => {
      store.linhaShake = null;
    }, 480);
  }
  if (M.tipo === "expulso") {
    store.mostrarToast(M.mensagem || "Você foi removido da sala.", true);
    store.voltarInicio();
    return;
  }
  if (M.tipo === "conectado" || M.tipo === "estadoSala") {
    store.atualizarArena(M.dados);
  }
}

export async function sincronizarArenaHttp(store) {
  if (!store.codigoSala || !store.idJogador) return;
  try {
    const R = await api.salaEstado(store.codigoSala, store.idJogador);
    if (!R.ok) {
      if (R.status === 404) {
        store.mostrarToast("Sala não encontrada.", true);
        pararSyncArena();
      }
      return;
    }
    const D = await R.json();
    if (
      store.modo === "arena" &&
      D.partidaEncerrada &&
      D.estadoSala === "encerrada"
    ) {
      store.dadosSala = D;
      store.atualizarArena(D);
      return;
    }
    if (D.estadoSala === "aguardando") {
      store.dadosSala = D;
      if (store.view !== "jogo") {
        store.irParaView(store.modo === "ranqueada" ? "inicio" : "arenaLobby");
      }
    } else {
      store.atualizarArena(D);
    }
  } catch {
    /* rede */
  }
}

export function iniciarSyncArena(store) {
  pararSyncArena();
  sincronizarArenaHttp(store);
  intervaloSyncArena = setInterval(() => sincronizarArenaHttp(store), 2500);
  iniciarPingArena(store);
}

export function conectarWsArena(store) {
  if (!store.codigoSala || !store.idJogador) return;
  store.pararLobbyWs();
  const url = UrlWebSocket(
    `/ws/sala/${store.codigoSala}/${store.idJogador}`
  );
  if (
    socketSala &&
    store.wsUrl === url &&
    (socketSala.readyState === WebSocket.OPEN ||
      socketSala.readyState === WebSocket.CONNECTING)
  ) {
    iniciarSyncArena(store);
    return;
  }
  fecharSocketSala();
  store.wsUrl = url;
  socketSala = new WebSocket(url);
  iniciarSyncArena(store);

  socketSala.onopen = () => {
    store.tentativasReconexao = 0;
    store.bannerReconexao = false;
    store.wsConectado = true;
    sincronizarArenaHttp(store);
  };
  socketSala.onmessage = (e) => {
    try {
      processarWsArena(store, JSON.parse(e.data));
    } catch {
      /* inválido */
    }
  };
  socketSala.onerror = () => {
    store.bannerReconexao = true;
    store.wsConectado = false;
  };
  socketSala.onclose = () => {
    store.wsConectado = false;
    if (
      !EhModoSalaOnline(store.modo) ||
      !store.codigoSala ||
      !store.idJogador ||
      store.encerrada ||
      store.view === "inicio"
    ) {
      pararSyncArena();
      return;
    }
    store.bannerReconexao = true;
    if (store.tentativasReconexao < 12) {
      store.tentativasReconexao++;
      const espera = Math.min(1500 * store.tentativasReconexao, 8000);
      setTimeout(() => conectarWsArena(store), espera);
      return;
    }
    aoReconexaoWsEsgotada(store);
  };
}
