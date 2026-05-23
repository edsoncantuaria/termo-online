import { CHAVE_SESSAO, CHAVE_CODIGO_SALA, CHAVE_NICK } from "./constantes.js";
import { EhModoSalaOnline } from "./modos.js";

export function ObterSessao() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE_SESSAO) || "null");
  } catch {
    return null;
  }
}

export function LimparSessao() {
  localStorage.removeItem(CHAVE_SESSAO);
  LimparCodigoSala();
}

/** Campo "Código" da home não persiste; remove legado do localStorage. */
export function LimparCodigoSala() {
  localStorage.removeItem(CHAVE_CODIGO_SALA);
}

export function CarregarNickLocal() {
  return localStorage.getItem(CHAVE_NICK) || "Jogador";
}

export function SalvarNickLocal(Nick) {
  localStorage.setItem(CHAVE_NICK, Nick);
}

export function MontarPayloadSessao(Estado) {
  const dados = {};
  if (
    Estado.modo === "ranqueada" &&
    Estado.codigoSala &&
    Estado.idJogador &&
    !Estado.encerrada
  ) {
    dados.ranqueada = {
      codigoSala: Estado.codigoSala,
      idJogador: Estado.idJogador,
      souCriador: Estado.souCriador,
      configuracao: Estado.configArena,
      view: Estado.view === "jogo" ? "jogo" : "inicio",
    };
  } else if (
    Estado.modo === "arena" &&
    Estado.codigoSala &&
    Estado.idJogador &&
    !Estado.encerrada
  ) {
    dados.arena = {
      codigoSala: Estado.codigoSala,
      idJogador: Estado.idJogador,
      souCriador: Estado.souCriador,
      configuracao: Estado.configArena,
      view: Estado.view === "jogo" ? "jogo" : "arenaLobby",
    };
  }
  if (
    Estado.idPartida &&
    !Estado.encerrada &&
    Estado.modo &&
    !EhModoSalaOnline(Estado.modo)
  ) {
    dados.solo = {
      modo: Estado.modo,
      idPartida: Estado.idPartida,
      tokenPartida: Estado.tokenPartida,
      dataDia: Estado.dataDia,
      tentativa: Estado.tentativa,
      letras: Estado.letras,
      indiceCursor: Estado.indiceCursor ?? 0,
      tentativasHist: Estado.tentativasHist,
      teclado: Estado.teclado,
      maximoTentativas: Estado.maxTentativas,
    };
  }
  return dados.arena || dados.ranqueada || dados.solo ? dados : null;
}

export function PersistirSessao(Estado) {
  const dados = MontarPayloadSessao(Estado);
  if (dados) localStorage.setItem(CHAVE_SESSAO, JSON.stringify(dados));
  else LimparSessao();
}
