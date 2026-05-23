import { CHAVE_SESSAO, CHAVE_CODIGO_SALA, CHAVE_NICK } from "./constantes.js";
import { EhModoSalaOnline } from "./modos.js";

const CANAL_SESSAO =
  typeof BroadcastChannel !== "undefined"
    ? new BroadcastChannel("termo-sessao")
    : null;

export function NotificarSessaoAlteradaEmOutrasAbas() {
  CANAL_SESSAO?.postMessage({ tipo: "sessaoAtualizada", em: Date.now() });
}

export function RegistrarListenerSessaoOutrasAbas(callback) {
  if (!CANAL_SESSAO || typeof callback !== "function") return () => {};
  const handler = (ev) => {
    if (ev.data?.tipo === "sessaoAtualizada") callback();
  };
  CANAL_SESSAO.addEventListener("message", handler);
  return () => CANAL_SESSAO.removeEventListener("message", handler);
}

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
  /** Arena/ranqueada: `encerrada` só indica fim da rodada do jogador, não fim da sessão. */
  const sessaoOnlineAtiva =
    EhModoSalaOnline(Estado.modo) &&
    Estado.codigoSala &&
    Estado.idJogador &&
    !Estado.dadosSala?.partidaEncerrada;

  const DadosSala = Estado.dadosSala || {};
  const credenciaisOnline = {
    codigoSala: Estado.codigoSala,
    idJogador: Estado.idJogador,
    idPartida: Estado.idPartida,
    tokenSessao: Estado.tokenSessao,
    souCriador: Estado.souCriador,
    configuracao: Estado.configArena,
    estadoSala: DadosSala.estadoSala || Estado.estadoSalaArena,
    pausada: !!(DadosSala.pausada || DadosSala.estadoSala === "pausada"),
    segundosPausaRestantes: DadosSala.segundosPausaRestantes ?? null,
    segundosAteAbandono: DadosSala.segundosAteAbandono ?? null,
    souJogadorPausado: !!DadosSala.souJogadorPausado,
  };
  if (Estado.modo === "ranqueada" && sessaoOnlineAtiva) {
    dados.ranqueada = {
      ...credenciaisOnline,
      view: Estado.view === "jogo" ? "jogo" : "inicio",
    };
  } else if (
    Estado.modo === "arena" &&
    Estado.codigoSala &&
    Estado.idJogador &&
    !Estado.dadosSala?.partidaEncerrada
  ) {
    dados.arena = {
      ...credenciaisOnline,
      view:
        Estado.view === "jogo" && sessaoOnlineAtiva
          ? "jogo"
          : "arenaLobby",
      partidaEncerrada: !!Estado.dadosSala?.partidaEncerrada,
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
    if (Estado.modo === "pratica" && Estado.palavraSecreta) {
      dados.solo.palavraSecreta = Estado.palavraSecreta;
    }
  }
  return dados.arena || dados.ranqueada || dados.solo ? dados : null;
}

export function PersistirSessao(Estado) {
  const dados = MontarPayloadSessao(Estado);
  if (dados) {
    localStorage.setItem(CHAVE_SESSAO, JSON.stringify(dados));
    NotificarSessaoAlteradaEmOutrasAbas();
  } else LimparSessao();
}
