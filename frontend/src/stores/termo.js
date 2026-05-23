import { defineStore } from "pinia";
import { UrlWebSocket } from "../config/origem.js";
import { api } from "../services/api.js";
import {
  TAMANHO_PALAVRA,
  TECLADO_LINHAS,
  CHAT_VIDA_MS,
  CHAT_MAX_VISIVEIS,
  BALAO_FALA_MS,
  BALAO_FALA_SAIDA_MS,
  DURACAO_TOAST_MS,
  CHAVE_TUTORIAL_VISTO,
  CHAVE_TUTORIAL_MULTI,
  CHAVE_SESSAO,
} from "../utils/constantes.js";
import { TextoProximaDiaria } from "../utils/diaria.js";
import {
  CarregarAuthLocal,
  SalvarAuthLocal,
  LimparAuthLocal,
} from "../utils/auth.js";
import {
  ValidarNick,
  ValidarLogin,
  ValidarRegistro,
  NormalizarNick,
} from "../utils/validacao-auth.js";
import {
  EhModoSalaOnline,
  EhJogoAtivoOnline,
  PartidaArenaEmRodada,
  PartidaRanqueadaAtiva,
} from "../utils/modos.js";
import {
  NormalizarTentativa,
  RegistrarLetrasNoTeclado,
  LetrasEmProgressoSalvas,
  LetrasVazias,
  NormalizarLetrasProgresso,
  LetrasPreenchidas,
  MontarPalavraChute,
  PalavraJaFoiTentada,
  ProximoIndiceVazio,
  FormatarCronometro,
  ModoVitoriasArena,
  GerarTextoCompartilhar,
  MontarResultadoUi,
  EhErroNick,
} from "../utils/jogo.js";
import {
  TextoStatusLobby,
  ChipsConfigLobby,
  NickExibicao,
} from "../utils/jogador.js";
import {
  CalcularInstigacaoSerie,
  ChaveInstigacaoSerie,
} from "../utils/instigacao-serie.js";
import { TextoXpGanho } from "../utils/progresso.js";
import {
  AvatarEfetivo,
  AvatarValido,
  SalvarAvatarLocal,
} from "../utils/avatares.js";
import { acoesRanqueada } from "./termo/acoes-ranqueada.js";
import { acoesJogoAtivo } from "./termo/acoes-jogo-ativo.js";
import { acoesSolo } from "./termo/acoes-solo.js";
import {
  enviarChutePraticaLocal,
  restaurarPraticaLocal,
} from "./termo/acoes-pratica-local.js";
import { acoesResultado } from "./termo/acoes-resultado.js";
import {
  ObterSessao,
  LimparSessao,
  PersistirSessao,
  RegistrarListenerSessaoOutrasAbas,
  LimparCodigoSala,
  CarregarNickLocal,
  SalvarNickLocal,
} from "../utils/sessao.js";
import {
  CodigoConviteConflita,
  DeveIgnorarSincronizacaoOutraAba,
  SolicitarRetomarSessao,
} from "../utils/sincronizacao-sessao.js";
import {
  ObterStats,
  SalvarStats,
} from "../utils/stats.js";
import {
  ObterPreferencias,
  SalvarPreferencias,
  AplicarDaltonismo,
  AplicarTema,
  ObservarTemaSistema,
} from "../lib/extras.js";
import { GarantirCacheDicionario } from "../utils/dicionario-cache.js";
import {
  AplicarTempoServidor,
  DataDiaServidor,
  SincronizarTempoServidor,
} from "../utils/tempo-servidor.js";
import { SalvarInstanciaLocal } from "../utils/auth.js";
import * as acoesArena from "./termo/acoes-arena.js";
import { TocarSom, prepararSons } from "../lib/som.js";
import {
  LimparCacheAplicacao,
  LimparCachesPwa,
  LimparLocalStorageCompleto,
} from "../utils/cache-local.js";
import { AgendarFimAnimacao, DURACAO_FLIP_LINHA } from "../utils/animacao.js";

function JogadorEuNaSala(Estado) {
  return Estado.dadosSala?.jogadores?.find((j) => j.souEu) ?? null;
}

/** Arena/ranqueada: edição depende do estado da rodada, não só de `encerrada`. */
function PodeEditarGradeAtualEstado(Estado) {
  if (Estado.view !== "jogo" || Estado.espectador) return false;
  if (EhModoSalaOnline(Estado.modo)) {
    if (Estado.estadoSalaArena === "pausada") return false;
    return (
      Estado.estadoSalaArena === "jogando" &&
      !JogadorEuNaSala(Estado)?.finalizou
    );
  }
  return !Estado.encerrada;
}

let socketLobby = null;
let tentativasReconexaoLobby = 0;
let intervaloLobbyHttpFallback = null;

function pararLobbyHttpFallback() {
  if (intervaloLobbyHttpFallback) {
    clearInterval(intervaloLobbyHttpFallback);
    intervaloLobbyHttpFallback = null;
  }
}
let intervaloTimer = null;
let timersChat = new Map();
let timerBalaoFala = null;
const chavesChatVistas = new Set();
let intervaloCountdown = null;
let intervaloPausa = null;
let cacheDicionarioSet = null;
let listenerSessaoOutraAba = null;
let listenerVisibilidadeApp = null;

function PararIntervaloCountdown() {
  if (intervaloCountdown) {
    clearInterval(intervaloCountdown);
    intervaloCountdown = null;
  }
}

function PararIntervaloPausa() {
  if (intervaloPausa) {
    clearInterval(intervaloPausa);
    intervaloPausa = null;
  }
}
let pararObservadorTema = null;
let timerToast = null;
let listenerPersistirPagina = null;

function ChaveMsgChat(M) {
  return `${M.quando}|${M.idJogador}|${M.texto}`;
}

export const useTermoStore = defineStore("termo", {
  state: () => ({
    view: "inicio",
    nick: CarregarNickLocal(),
    codigoEntrada: "",
    /** Código de ?sala= preservado após limpar a URL (evita perder no 2º init). */
    conviteSalaCodigo: "",
    processandoConviteSala: false,
    senhaEntrada: "",
    espectadorEntrada: false,

    toast: "",
    toastErro: false,
    toastSucesso: false,
    carregandoHome: false,
    carregandoPerfil: false,
    carregandoChute: false,
    linhaShake: null,
    filtroSalasPublicas: "todas",
    mostrarTutorial: false,
    conta: CarregarAuthLocal().conta,
    token: CarregarAuthLocal().token,
    filaRanqueada: false,
    filaSegundos: null,
    filaFase: null,
    filaMensagem: "",
    filaJogadoresNaFila: 0,
    filaJogadoresOnline: null,
    filaPreview: [],
    filaBusca: null,
    filaPodeCancelar: true,
    jogoAtivo: null,
    carregandoJogoAtivo: false,
    minhaPosicaoRanqueada: null,
    totalRanqueados: 0,
    rankingRanqueado: [],
    historicoRanqueado: [],
    temporadaRanqueada: null,
    filaUltimoContagemNaFila: 0,
    bannerReconexao: false,
    ultimaPartidaResultadoExibida: null,
    wsConectado: false,
    lobbyWsConectado: false,
    lobbyWsReconectando: false,

    modo: null,
    idPartida: null,
    /** Prática local: palavra secreta (não enviar ao servidor). */
    palavraSecreta: null,
    tokenPartida: null,
    tokenSessao: null,
    dataDia: null,
    maxTentativas: 6,
    tentativa: 0,
    letras: LetrasVazias(),
    indiceCursor: 0,
    encerrada: false,
    teclado: {},
    tentativasHist: [],
    tabuleiros: null,
    labelModo: "Prática",
    gradesMulti: [],

    codigoSala: null,
    idJogador: null,
    souCriador: false,
    configArena: null,
    estadoSalaArena: null,
    dadosSala: null,
    espectador: false,
    arenaTentativas: [],
    arenaTentativasExibidas: 0,
    arenaRodadaSync: null,
    ultimoVencedorRodadaId: null,
    ultimoToastRodadaFim: null,

    diariaBadge: "Hoje",
    diariaFeita: false,
    diariaBtnTexto: "Jogar",

    statsLocais: ObterStats(),
    statsServidor: null,
    salasPublicas: [],
    historicoDiaria: [],
    /** eu | outro — perfil do modal */
    perfilVisualizacao: "eu",
    perfilOutro: null,
    carregandoPerfilOutro: false,

    preferencias: ObterPreferencias(),
    frasesChat: [],

    chatMensagens: [],
    /** Balão de fala no topo (chat rápido), por jogador. */
    balaoFala: null,
    cronometroTexto: "",
    cronometroUrgente: false,
    cronometroVisivel: false,
    countdownSegundos: null,
    toastVitoriaRodada: "",
    ultimaInstigacaoSerieChave: null,

    dialogAberto: null,
    dialogAvatarAberto: false,
    dialogContaModo: "entrada",
    dialogContaForcarRegistro: false,
    /** Abre direto o formulário (login/registro), sem tela de visitante. */
    dialogContaIrDiretoForm: false,
    dialogContaNickSugerido: "",
    dificuldade: "normal",
    codigoDesafio: "",

    aviso: {
      titulo: "Atenção",
      mensagem: "",
      dica: "",
      tipo: "info",
      textoBotao: "Entendi",
      textoBotaoSec: "Cancelar",
      nickTemp: "",
      senhaTemp: "",
      conviteCodigo: "",
      exigeSenha: false,
      aoConfirmar: null,
      aoCancelar: null,
    },

    resultado: {
      titulo: "Resultado",
      texto: "",
      pontos: "",
      confete: false,
      confeteIntenso: false,
      gradeTexto: "",
      mostrarGrade: false,
      mostrarCopiar: false,
      mostrarCompartilhar: false,
      mostrarRevanche: false,
      ehDiaria: false,
      modo: null,
      venceu: null,
      tentativasUsadas: null,
      maxTentativas: 6,
      dataDia: null,
      dataFormatada: "",
    },

    formCriarSala: {
      maxJogadores: 4,
      mesmaPalavra: false,
      verOutros: true,
      modoSessao: "vitorias",
      metaVitorias: 3,
      inicioAutoDois: false,
      tempoLimite: 180,
      senha: "",
    },

    formConfigurarSala: {
      minJogadores: 2,
      maxJogadores: 4,
      mesmaPalavra: true,
      verOutros: true,
      modoSessao: "pontos",
      metaVitorias: 5,
      inicioAutoDois: false,
      tempoLimite: 180,
      temSenhaAtual: false,
      senhaNova: "",
      removerSenha: false,
    },

    tentativasReconexao: 0,
    wsUrl: null,
  }),

  getters: {
    deveExibirTutorial: (s) => {
      if (s.conviteSalaCodigo || s.processandoConviteSala) return false;
      if (
        s.dialogAberto === "aviso" &&
        (s.aviso.tipo === "convite" || s.aviso.tipo === "senhaSala")
      ) {
        return false;
      }
      return s.mostrarTutorial;
    },
    filaRanqueadaTravada: (s) => !!s.filaRanqueada,
    filaRanqueadaPodeCancelar: (s) =>
      !!s.filaRanqueada && !!s.filaPodeCancelar && s.filaFase !== "conectando",
    /** Conta com e-mail (não visitante) — exige diária e ranqueado. */
    contaRegistrada: (s) => !!(s.conta?.podeRanqueada),
    nickJogo: (s) => {
      const N = (s.conta?.nick || s.nick || "Jogador").trim().slice(0, 24);
      return N || "Jogador";
    },
    tecladoLinhas: () => [
      TECLADO_LINHAS[0],
      TECLADO_LINHAS[1],
      [...TECLADO_LINHAS[2], "back"],
      ["enter"],
    ],
    emJogo: (s) => s.view === "jogo",
    emLobby: (s) => s.view === "arenaLobby",
    modoJogoArena: (s) => s.view === "jogo" && EhModoSalaOnline(s.modo),
    modoJogoRanqueada: (s) => s.view === "jogo" && s.modo === "ranqueada",
    partidaRanqueadaAtiva: (s) => PartidaRanqueadaAtiva(s),
    partidaArenaEmRodada: (s) => PartidaArenaEmRodada(s),
    modoMulti: (s) => (s.tabuleiros?.length || 0) > 1,
    mostrarGradePrincipal: (s) =>
      s.emJogo && (!s.modoMulti || EhModoSalaOnline(s.modo)) && !s.espectador,
    mostrarGradesMulti: (s) =>
      s.emJogo && s.modoMulti && !EhModoSalaOnline(s.modo),
    lobbyStatus: (s) => {
      if (!s.dadosSala) return "Conectando…";
      return TextoStatusLobby({
        ...s.dadosSala,
        souCriador: s.dadosSala.souCriador ?? s.souCriador,
      });
    },
    lobbyChips: (s) => (s.dadosSala ? ChipsConfigLobby(s.dadosSala) : []),
    lobbyJogadores: (s) =>
      s.dadosSala?.jogadores || [
        {
          nomeJogador: s.conta?.nick || s.nick,
          souEu: true,
          idJogador: s.idJogador,
        },
      ],
    podeIniciarArena: (s) =>
      s.dadosSala?.estadoSala === "aguardando" &&
      !!(s.dadosSala?.souCriador ?? s.souCriador) &&
      !!s.dadosSala?.podeIniciar,
    euProntoLobby: (s) => {
      const eu = s.lobbyJogadores.find((j) => j.souEu);
      return !!eu?.pronto;
    },
    motivoNaoIniciarArena: (s) => s.dadosSala?.motivoNaoIniciar || "",
    badgeConexaoVisivel: (s) =>
      s.modo === "arena" && !!s.codigoSala && s.view === "arenaLobby",
    tituloTopo: (s) => {
      if (s.view === "arenaLobby") return "Sala de espera";
      if (s.view === "jogo") {
        if (s.modo === "diaria") return "Palavra do dia";
        if (s.modo === "ranqueada") return "Ranqueado";
        if (s.modo === "arena") return "Arena";
        return "Prática";
      }
      return "Termo";
    },
    subtituloTopo: (s) => {
      if (s.view === "jogo") {
        const tempo =
          EhModoSalaOnline(s.modo) && s.configArena?.tempoLimiteTexto
            ? ` · ${s.configArena.tempoLimiteTexto}`
            : "";
        const duelo =
          s.modo === "ranqueada"
            ? " · melhor de 3 (até 3 mapas)"
            : "";
        return `6 tentativas · 5 letras${tempo}${duelo}`;
      }
      if (s.view === "arenaLobby") {
        return s.codigoSala
          ? `Código ${s.codigoSala}`
          : "Aguardando jogadores";
      }
      return "Palavras em português";
    },
    outrosNaRodada: (s) => {
      const j = s.dadosSala?.jogadores || [];
      if (s.espectador) return j.filter((x) => !x.espectador);
      return j.filter((x) => !x.souEu);
    },
    tituloOutros: (s) => {
      const n = s.outrosNaRodada.length;
      if (s.espectador) {
        if (!n) return "Assistindo";
        return n === 1
          ? "Assistindo · 1 jogador"
          : `Assistindo · ${n} jogadores`;
      }
      if (!n) return "Na rodada";
      return n === 1
        ? "Na rodada · 1 jogador"
        : `Na rodada · ${n} jogadores`;
    },
    lateralVisivel: (s) =>
      s.modoJogoArena &&
      (s.outrosNaRodada.length > 0 || s.emJogo),
    painelChatVisivel: (s) => s.modoJogoArena,
    /** Só envia nova frase quando o seu balão de fala sumir. */
    podeEnviarChatRapido: (s) => {
      if (!s.idJogador || s.espectador) return false;
      if (!s.balaoFala) return true;
      return s.balaoFala.idJogador !== s.idJogador;
    },
    painelEntreRodadas: (s) =>
      s.dadosSala?.estadoSala === "entre_rodadas" &&
      !s.dadosSala?.partidaEncerrada,
    badgeEstadoJogo: (s) => {
      const D = s.dadosSala;
      if (!D || !EhModoSalaOnline(s.modo)) return null;
      if (s.espectador) {
        if (D.partidaEncerrada) {
          return { tipo: "aguardo", texto: "Partida encerrada" };
        }
        if (D.estadoSala === "jogando") {
          return { tipo: "prep", texto: "Assistindo a rodada" };
        }
        if (D.estadoSala === "entre_rodadas") {
          return { tipo: "pausa", texto: "Rodada encerrada — assistindo" };
        }
        return { tipo: "prep", texto: "Modo espectador" };
      }
      if (D.estadoSala === "pausada" || D.pausada) {
        const seg = D.segundosPausaRestantes;
        const txt =
          seg != null
            ? `Partida pausada — retorno em até ${seg}s`
            : D.motivoPausa || "Partida pausada";
        return { tipo: "pausa", texto: txt };
      }
      if (D.estadoSala === "entre_rodadas") {
        return { tipo: "pausa", texto: "Rodada encerrada" };
      }
      if (D.estadoSala === "countdown") {
        const mapa = D.rodadaAtual || 1;
        const txtRanq =
          s.modo === "ranqueada" || D.configuracao?.ranqueada
            ? `Mapa ${mapa} de 3 · melhor de 3`
            : "Próxima rodada em instantes…";
        return { tipo: "prep", texto: txtRanq };
      }
      if (D.estadoSala === "jogando") {
        const eu = D.jogadores?.find((j) => j.souEu);
        if (eu?.venceu) return { tipo: "ok", texto: "Você acertou a palavra!" };
        if (eu?.finalizou) return { tipo: "aguardo", texto: "Aguardando outros jogadores" };
        return { tipo: "ativo", texto: "Rodada em andamento" };
      }
      return null;
    },
    balaoInstigacaoSerie: () => null,
    palavraReveladaArena: (s) => {
      const D = s.dadosSala;
      if (!D?.palavraRevelada || D.estadoSala !== "entre_rodadas") return "";
      return D.palavraRevelada;
    },
    placarArenaEnriquecido: (s) => {
      const lista = s.placarArena || [];
      if (!lista.length) return [];
      const porVitorias = s.porVitoriasArena;
      const meta = s.metaVitoriasArena || 5;
      const maxPts = Math.max(
        1,
        ...lista.map((j) => j.pontosAcumulados || 0)
      );
      return lista.map((j, i) => {
        let linha = {
          ...j,
          posicao: i + 1,
          progresso: porVitorias
            ? Math.min(100, ((j.vitoriasRodada || 0) / meta) * 100)
            : Math.min(100, ((j.pontosAcumulados || 0) / maxPts) * 100),
        };
        if (
          j.idJogador === s.idJogador &&
          s.conta?.podeRanqueada &&
          (j.semRank || !j.rotuloRank)
        ) {
          linha = {
            ...linha,
            rotuloRank: s.conta.rotuloRank,
            eloNome: s.conta.eloNome,
            elo: s.conta.elo,
            eloClasse: s.conta.eloClasse,
            semRank: s.conta.semRank,
            pontosRanqueada: s.conta.pontosRanqueada,
          };
        }
        return linha;
      });
    },
    podeEditarGradeAtual: (s) => PodeEditarGradeAtualEstado(s),
    podeMoverCursorGrade: (s) => PodeEditarGradeAtualEstado(s),
    mostrarDicaCelulas: (s) => {
      if (!PodeEditarGradeAtualEstado(s) || !s.mostrarGradePrincipal) return false;
      return !LetrasPreenchidas(s.letras);
    },
    mensagemAguardoArena: (s) => {
      const D = s.dadosSala;
      if (!D || !EhModoSalaOnline(s.modo) || s.espectador) return "";
      if (D.estadoSala === "entre_rodadas" && !D.partidaEncerrada) {
        if (!D.podeProximaRodada) {
          return "Aguardando o host iniciar a próxima rodada…";
        }
        return "";
      }
      if (D.estadoSala === "jogando") {
        const eu = D.jogadores?.find((j) => j.souEu);
        if (eu?.finalizou && !eu?.venceu) {
          return "Você finalizou. Aguardando os outros jogadores…";
        }
        if (eu?.venceu) {
          return "Você acertou! Aguardando o fim da rodada…";
        }
      }
      return "";
    },
    placarArena: (s) => s.dadosSala?.placar || [],
    porVitoriasArena: (s) =>
      s.dadosSala ? ModoVitoriasArena(s.dadosSala) : false,
    metaVitoriasArena: (s) =>
      s.dadosSala?.metaVitorias ||
      s.dadosSala?.configuracao?.metaVitorias ||
      5,
    rodadaInfoTexto: (s) => {
      const D = s.dadosSala;
      if (!D) return "";
      const modoTxt = D.modoSessaoTexto || D.modoRodadasTexto || "";
      if (D.partidaEncerrada) return "Sessão finalizada";
      if (D.estadoSala === "entre_rodadas") {
        return s.porVitoriasArena
          ? `Rodada ${D.rodadaAtual} — ${modoTxt}`
          : "Maratona — placar acumulado";
      }
      if (D.estadoSala === "jogando") {
        return s.porVitoriasArena
          ? `Rodada ${D.rodadaAtual} · ${modoTxt}`
          : `Rodada ${D.rodadaAtual} — maratona`;
      }
      return modoTxt;
    },
    pillModoTexto: (s) => {
      if (EhModoSalaOnline(s.modo) && s.dadosSala?.rodadaAtual) {
        const eu = s.dadosSala.placar?.find((j) => j.idJogador === s.idJogador);
        const meta = s.metaVitoriasArena;
        const prefixo = s.modo === "ranqueada" ? "Ranqueado" : "Arena";
        if (s.modo === "ranqueada" && s.porVitoriasArena) {
          const opp = s.dadosSala.placar?.find(
            (j) => j.idJogador !== s.idJogador
          );
          const a = eu?.vitoriasRodada || 0;
          const b = opp?.vitoriasRodada || 0;
          const mapa = s.dadosSala.rodadaAtual || 1;
          return `${prefixo} · ${a}–${b} · mapa ${mapa}/3`;
        }
        return s.porVitoriasArena
          ? `${prefixo} · ${eu?.vitoriasRodada || 0}/${meta} vit.`
          : `${prefixo} · R${s.dadosSala.rodadaAtual}`;
      }
      return s.labelModo;
    },
    linhasGradePrincipal: (s) => {
      const max = s.maxTentativas;
      const linhas = [];
      for (let i = 0; i < max; i++) {
        if (i < s.tentativa) {
          const tent =
            EhModoSalaOnline(s.modo)
              ? NormalizarTentativa(s.arenaTentativas[i])
              : NormalizarTentativa(s.tentativasHist[i]);
          linhas.push({
            ...tent,
            revelada: true,
            animar: !!tent?.animar,
          });
        } else if (
          i === s.tentativa &&
          PodeEditarGradeAtualEstado(s)
        ) {
          const letras = NormalizarLetrasProgresso(s.letras);
          const temDica = Object.values(s.teclado || {}).includes("presente");
          linhas.push({
            letras,
            estados: [],
            atual: true,
            revelada: false,
            comDica: temDica,
            indiceCursor: s.indiceCursor,
          });
        } else {
          linhas.push({
            letras: Array(TAMANHO_PALAVRA).fill(""),
            estados: [],
            atual: false,
            revelada: false,
          });
        }
      }
      return linhas;
    },
    dotsTentativas: (s) =>
      Array.from({ length: s.maxTentativas }, (_, i) => ({
        usada: i < s.tentativa,
        atual: i === s.tentativa && PodeEditarGradeAtualEstado(s),
      })),
    statVitorias: (s) => s.statsLocais.vitorias || 0,
    statSequencia: (s) => s.statsLocais.sequencia || 0,
    statDiaria: (s) =>
      s.diariaFeita ? (s.statsLocais.diariaVenceu ? "✓" : "—") : "—",
    statTaxa: (s) =>
      s.statsServidor ? `${s.statsServidor.taxaVitoria || 0}%` : "—",
    statsExtraTexto: (s) =>
      s.statsServidor
        ? `${s.statsServidor.partidasRanking || 0} partidas no ranking · ${s.statsServidor.diariasVencidas || 0} diárias ganhas (14d)`
        : "",
    linkSalaAtual: (s) =>
      s.codigoSala
        ? `${location.origin}/?sala=${s.codigoSala}`
        : location.origin,
    proximaDiariaTexto: () => TextoProximaDiaria(),
    salasPublicasFiltradas: (s) => {
      let lista = s.salasPublicas || [];
      if (s.filtroSalasPublicas === "vaga") {
        lista = lista.filter((x) => x.temVaga !== false);
      } else if (s.filtroSalasPublicas === "pontos") {
        lista = lista.filter((x) => x.modoSessao === "pontos");
      } else if (s.filtroSalasPublicas === "vitorias") {
        lista = lista.filter((x) => x.modoSessao === "vitorias");
      }
      return lista;
    },
  },

  actions: {
    mostrarToast(texto, erro = false, sucesso = false) {
      if (timerToast) {
        clearTimeout(timerToast);
        timerToast = null;
      }
      this.toast = texto;
      this.toastErro = !!erro && !!texto;
      this.toastSucesso = !!sucesso && !!texto;
      if (texto) {
        const msg = texto;
        timerToast = setTimeout(() => {
          timerToast = null;
          if (this.toast === msg) {
            this.toast = "";
            this.toastErro = false;
            this.toastSucesso = false;
          }
        }, DURACAO_TOAST_MS);
      }
    },

    tratarChuteInvalido(mensagem) {
      const online = EhModoSalaOnline(this.modo);
      if (online) {
        acoesArena.cancelarTimeoutChuteOnline();
        this.carregandoChute = false;
      } else {
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
      }
      if (this.modo && !EhModoSalaOnline(this.modo) && this.idPartida) {
        this.persistir();
      }
      this.mostrarToast(mensagem, true);
      TocarSom("erro");
      this.linhaShake = this.tentativa;
      setTimeout(() => {
        this.linhaShake = null;
      }, 480);
    },

    confirmarVoltarInicio() {
      if (this.view === "inicio" && !this.partidaRanqueadaAtiva) {
        return Promise.resolve();
      }
      let titulo = "Sair?";
      let mensagem = null;
      let dica = null;
      if (this.view === "arenaLobby" || (this.modo === "arena" && this.codigoSala)) {
        titulo = "Sair da sala?";
        mensagem = "Você será removido da partida.";
        dica = "Para voltar depois, peça o código da sala ao host.";
      } else if (this.view === "jogo" && !this.encerrada && !EhModoSalaOnline(this.modo)) {
        titulo = "Abandonar partida?";
        mensagem = "O progresso desta partida solo será perdido.";
      } else if (
        ((this.view === "jogo" && EhModoSalaOnline(this.modo)) ||
          this.partidaRanqueadaAtiva ||
          this.partidaArenaEmRodada) &&
        !this.espectador &&
        !this.dadosSala?.partidaEncerrada
      ) {
        const ehRanq = this.modo === "ranqueada";
        titulo = ehRanq ? "Abandonar duelo ranqueado?" : "Sair da partida?";
        if (ehRanq) {
          const rp = this.conta?.pontosRanqueada ?? 0;
          const perda = Math.min(12, Math.max(8, 10));
          mensagem = `Você perderá o duelo e cerca de ${perda} pontos de RP (${rp} → ~${Math.max(0, rp - perda)}).`;
        } else {
          mensagem =
            "Você será removido desta partida e não poderá continuar nesta rodada.";
        }
        dica = ehRanq
          ? "O oponente vence a série. Para só pausar, feche a aba e use «Reconectar» na home."
          : null;
        return new Promise((resolve) => {
          this.mostrarConfirmacao({
            titulo,
            mensagem,
            dica,
            textoConfirmar: "Abandonar e ir ao início",
            textoCancelar: "Continuar jogando",
            aoConfirmar: () => {
              this.desistirPartida().finally(resolve);
            },
            aoCancelar: () => resolve(),
          });
        });
      }
      if (!mensagem) return this.voltarInicio();
      return new Promise((resolve) => {
        this.mostrarConfirmacao({
          titulo,
          mensagem,
          dica,
          textoConfirmar: "Sair",
          textoCancelar: "Continuar",
          aoConfirmar: () => {
            this.voltarInicio().finally(resolve);
          },
          aoCancelar: () => resolve(),
        });
      });
    },

    fecharTutorial() {
      this.mostrarTutorial = false;
      localStorage.setItem(CHAVE_TUTORIAL_VISTO, "1");
      if (!this.token && !this.conta) {
        this.abrirConta("entrada");
      }
    },

    definirPreferenciaTemaModo(modo) {
      const m = modo === "claro" || modo === "escuro" ? modo : "sistema";
      this.preferencias = {
        ...this.preferencias,
        temaModo: m,
        temaClaro: m === "claro",
      };
      SalvarPreferencias(this.preferencias);
      AplicarTema(this.preferencias);
    },

    definirPreferenciaTema(claro) {
      this.definirPreferenciaTemaModo(claro ? "claro" : "escuro");
    },

    definirPreferenciaAnimacao(reduzir) {
      this.preferencias = { ...this.preferencias, reduzirAnimacao: !!reduzir };
      SalvarPreferencias(this.preferencias);
      document.documentElement.classList.toggle(
        "reduzir-animacao",
        !!reduzir
      );
    },

    confirmarLimparCache() {
      this.mostrarConfirmacao({
        titulo: "Limpar cache local?",
        mensagem:
          "Remove sessão salva, dicionário em cache, estatísticas locais e flags de tutorial.",
        dica: "Sua conta (login) e preferências de som/tema são mantidas.",
        textoConfirmar: "Limpar",
        textoCancelar: "Cancelar",
        aoConfirmar: () => this.executarLimparCache(),
      });
    },

    async executarLimparCache() {
      LimparCacheAplicacao();
      await LimparCachesPwa().catch(() => {});
      cacheDicionarioSet = null;
      this.conviteSalaCodigo = "";
      this.limparChat();
      this.mostrarToast(
        "Cache local limpo. A página vai recarregar para buscar a versão nova.",
        false,
        true
      );
      if (typeof window !== "undefined") {
        setTimeout(() => window.location.reload(), 600);
      }
    },

    definirFiltroSalasPublicas(filtro) {
      this.filtroSalasPublicas = filtro;
    },

    aplicarProgressoResposta(D) {
      if (!D?.progresso || !this.conta || this.conta.ehVisitante) return;
      this.conta = { ...this.conta, progresso: D.progresso };
      SalvarAuthLocal(this.token, this.conta);
      const txt = TextoXpGanho(D);
      if (txt) this.mostrarToast(txt, false, true);
      if (D.novasBadges?.length) {
        const b = D.novasBadges[0];
        setTimeout(
          () =>
            this.mostrarToast(
              `Badge: ${b.nome} — ${b.descricao}`,
              false,
              true
            ),
          400
        );
      }
    },

    aplicarSessaoConta(conta, token, instanciaCliente) {
      this.conta = conta;
      this.token = token;
      SalvarAuthLocal(token, conta, instanciaCliente);
      if (instanciaCliente) SalvarInstanciaLocal(instanciaCliente);
      if (conta?.nick) {
        this.nick = conta.nick;
        SalvarNickLocal(conta.nick);
      }
    },

    /**
     * Atualiza perfil/instância no servidor sem deslogar.
     * Em 409 (instância antiga), reconcilia e mantém o token local.
     */
    async sincronizarContaServidor() {
      if (!this.token) return false;
      let D;
      try {
        D = await api.authEu();
      } catch (e) {
        if (e?.status === 409) {
          try {
            D = await api.authEuReconciliar();
          } catch (e2) {
            if (e2?.status === 401) this.authSair();
            return false;
          }
        } else if (e?.status === 401) {
          this.authSair();
          return false;
        } else {
          return true;
        }
      }
      const Local = CarregarAuthLocal();
      this.aplicarSessaoConta(
        D.conta,
        this.token,
        D.instanciaCliente ?? Local.instanciaCliente
      );
      return true;
    },

    avatarIdEfetivo() {
      return AvatarEfetivo(this.conta, this.nick);
    },

    async salvarAvatar(avatarId) {
      if (!AvatarValido(avatarId)) {
        this.mostrarToast("Avatar inválido.", true);
        return;
      }
      if (!this.conta) return;
      if (this.conta.ehVisitante) {
        SalvarAvatarLocal(avatarId);
        this.conta = { ...this.conta, avatarId };
        SalvarAuthLocal(this.token, this.conta);
        this.mostrarToast("Avatar atualizado!", false, true);
        return;
      }
      try {
        const D = await api.authAtualizarAvatar(avatarId);
        this.aplicarSessaoConta(D.conta, this.token);
        this.mostrarToast("Avatar salvo no perfil!", false, true);
      } catch (e) {
        this.mostrarToast(e.message || "Não foi possível salvar o avatar.", true);
      }
    },

    async authLogin(identificador, senha) {
      const V = ValidarLogin(identificador, senha);
      if (!V.ok) {
        this.mostrarToast(V.mensagem, true);
        return { ok: false, mensagem: V.mensagem };
      }
      if (
        this.token &&
        this.conta?.podeRanqueada &&
        !this.conta?.ehVisitante
      ) {
        await this.sincronizarContaServidor();
        this.fecharDialogs();
        this.mostrarToast(
          `Você já está logado como ${NickExibicao(this.conta.nick)}.`,
          false,
          true
        );
        return { ok: true };
      }
      try {
        const D = await api.authLogin(identificador, senha);
        this.aplicarSessaoConta(D.conta, D.token, D.instanciaCliente);
        this.fecharDialogs();
        this.mostrarToast(
          `Bem-vindo, ${NickExibicao(D.conta.nick)}!`,
          false,
          true
        );
        return { ok: true };
      } catch (e) {
        this.mostrarToast(e.message, true);
        return { ok: false, mensagem: e.message };
      }
    },

    async authRegistrar(nick, email, senha, confirmarSenha = senha) {
      const V = ValidarRegistro(nick, email, senha, confirmarSenha);
      if (!V.ok) {
        this.mostrarToast(V.mensagem, true);
        return { ok: false, mensagem: V.mensagem };
      }
      try {
        const D = await api.authRegistrar(V.nick, email, senha);
        this.aplicarSessaoConta(D.conta, D.token, D.instanciaCliente);
        this.fecharDialogs();
        this.mostrarToast("Conta criada com sucesso!", false, true);
      } catch (e) {
        this.mostrarToast(e.message, true);
        return { ok: false, mensagem: e.message };
      }
    },

    normalizarNickEntrada(valor) {
      return (valor || "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_]/g, "")
        .slice(0, 20);
    },

    async authVisitante(nickEscolhido) {
      const V = ValidarNick(nickEscolhido);
      if (!V.ok) {
        this.mostrarToast(V.mensagem, true);
        return { ok: false, mensagem: V.mensagem };
      }
      if (this.token && this.conta?.ehVisitante) {
        await this.sincronizarContaServidor();
        this.fecharDialogs();
        this.mostrarToast(
          `Você já está jogando como ${NickExibicao(this.conta.nick)}.`,
          false,
          true
        );
        return { ok: true };
      }
      try {
        const D = await api.authVisitante(V.nick);
        this.aplicarSessaoConta(D.conta, D.token, D.instanciaCliente);
        this.fecharDialogs();
        const exib = NickExibicao(D.conta.nick);
        const sufixo =
          D.conta.nick !== V.nick
            ? ` (${exib} — nome já em uso, variante atribuída)`
            : "";
        this.mostrarToast(
          `Você entrou como ${exib}${sufixo}`,
          false,
          true
        );
      } catch (e) {
        this.mostrarToast(e.message, true);
        return { ok: false, mensagem: e.message };
      }
    },

    exigirContaRegistrada() {
      if (this.conta?.podeRanqueada) return true;
      if (this.conta?.ehVisitante) this.abrirCriarConta();
      else this.abrirLoginConta();
      return false;
    },

    zerarEstadoPosLogout() {
      this.conta = null;
      this.token = null;
      this.modo = null;
      this.idPartida = null;
      this.tokenPartida = null;
      this.tokenSessao = null;
      this.codigoSala = null;
      this.idJogador = null;
      this.souCriador = false;
      this.espectador = false;
      this.espectadorEntrada = false;
      this.configArena = null;
      this.estadoSalaArena = null;
      this.dadosSala = null;
      this.jogoAtivo = null;
      this.carregandoJogoAtivo = false;
      this.encerrada = false;
      this.bannerReconexao = false;
      this.wsConectado = false;
      this.ultimaPartidaResultadoExibida = null;
      this.arenaTentativas = [];
      this.arenaTentativasExibidas = 0;
      this.arenaRodadaSync = null;
      this.tentativa = 0;
      this.letras = LetrasVazias();
      this.indiceCursor = 0;
      this.teclado = {};
      this.tentativasHist = [];
      this.tabuleiros = null;
      this.gradesMulti = [];
      acoesArena.cancelarTimeoutChuteOnline();
      this.carregandoChute = false;
      this.linhaShake = null;
      this.countdownSegundos = null;
      this.toastVitoriaRodada = "";
      this.filaRanqueada = false;
      this.filaSegundos = null;
      this.filaFase = null;
      this.filaMensagem = "";
      this.nick = "Jogador";
      this.codigoEntrada = "";
      this.senhaEntrada = "";
      this.statsLocais = {};
      this.preferencias = ObterPreferencias();
      AplicarDaltonismo(this.preferencias.daltonismo);
      AplicarTema(this.preferencias);
    },

    authSair() {
      const tokenAntes = this.token;
      const contaRegistrada =
        !!this.conta?.podeRanqueada && !this.conta?.ehVisitante;
      const codigo = this.codigoSala;
      const idJ = this.idJogador;
      const eraOnline = EhModoSalaOnline(this.modo);

      this.pararFilaRanqueada();
      PararIntervaloPausa();
      PararIntervaloCountdown();
      this.pararCronometro();
      this.limparChat();
      this.fecharDialogs();
      this.fecharSocketSala();
      this.pararLobbyWs();

      if (
        (this.partidaRanqueadaAtiva || this.partidaArenaEmRodada) &&
        this.idPartida &&
        idJ &&
        this.tokenSessao
      ) {
        api
          .partidaDesistir(this.idPartida, {
            idJogador: idJ,
            tokenSessao: this.tokenSessao,
          })
          .catch(() => {});
      } else if (eraOnline && codigo && idJ) {
        api.salaSair({ codigoSala: codigo, idJogador: idJ }).catch(() => {});
      }
      if (contaRegistrada && tokenAntes) {
        api.contaLimparJogoAtivo().catch(() => {});
      }

      this.zerarEstadoPosLogout();
      LimparLocalStorageCompleto();
      this.irParaView("inicio");
      this.mostrarToast(
        "Você saiu. Dados locais foram apagados para não retomar partida antiga.",
        false,
        true
      );
    },

    abrirConta(modo = "entrada", opcoes = {}) {
      this.dialogContaModo = modo;
      this.dialogContaForcarRegistro =
        modo === "registro" || !!opcoes.forcarRegistro;
      this.dialogContaIrDiretoForm = !!opcoes.irDiretoForm;
      if (opcoes.nickSugerido != null) {
        this.dialogContaNickSugerido = opcoes.nickSugerido;
      }
      this.abrirDialog("conta");
    },

    /** Login com e-mail/nick — usado nos modos que exigem conta. */
    abrirLoginConta() {
      this.dialogContaModo = "entrada";
      this.dialogContaForcarRegistro = false;
      this.dialogContaIrDiretoForm = true;
      this.abrirDialog("conta");
    },

    abrirCriarConta() {
      this.dialogContaModo = "registro";
      this.dialogContaForcarRegistro = true;
      this.dialogContaIrDiretoForm = true;
      this.dialogContaNickSugerido = this.conta?.nick || this.nick || "";
      this.abrirDialog("conta");
    },

    ...acoesRanqueada,
    ...acoesJogoAtivo,
    ...acoesSolo,
    ...acoesResultado,

    irParaView(nome) {
      this.view = nome;
      if (nome === "inicio") {
        this.codigoEntrada = "";
        this.fecharDialogs();
        this.conectarLobbyWs();
        this.carregarJogoAtivo();
      } else {
        this.pararLobbyWs();
      }
      if (nome !== "jogo") {
        PararIntervaloCountdown();
        this.countdownSegundos = null;
        this.pararCronometro();
      }
    },

    pararLobbyWs() {
      pararLobbyHttpFallback();
      if (socketLobby) {
        socketLobby.onclose = null;
        socketLobby.onerror = null;
        socketLobby.close();
        socketLobby = null;
      }
      tentativasReconexaoLobby = 0;
      this.lobbyWsConectado = false;
      this.lobbyWsReconectando = false;
    },

    conectarLobbyWs() {
      if (this.view !== "inicio") return;
      const url = UrlWebSocket("/ws/lobby");
      if (
        socketLobby &&
        (socketLobby.readyState === WebSocket.OPEN ||
          socketLobby.readyState === WebSocket.CONNECTING)
      ) {
        return;
      }
      if (socketLobby) {
        socketLobby.onclose = null;
        socketLobby.close();
      }
      socketLobby = new WebSocket(url);

      socketLobby.onopen = () => {
        tentativasReconexaoLobby = 0;
        pararLobbyHttpFallback();
        this.lobbyWsConectado = true;
        this.lobbyWsReconectando = false;
      };

      socketLobby.onmessage = (e) => {
        try {
          const M = JSON.parse(e.data);
          if (M.tipo === "salasPublicas" && Array.isArray(M.salas)) {
            this.salasPublicas = M.salas;
          }
        } catch {
          /* inválido */
        }
      };

      socketLobby.onerror = () => {
        this.lobbyWsConectado = false;
        this.lobbyWsReconectando = true;
      };

      socketLobby.onclose = () => {
        this.lobbyWsConectado = false;
        if (this.view !== "inicio") {
          this.lobbyWsReconectando = false;
          return;
        }
        this.lobbyWsReconectando = true;
        if (tentativasReconexaoLobby < 10) {
          tentativasReconexaoLobby++;
          const espera = Math.min(1500 * tentativasReconexaoLobby, 8000);
          setTimeout(() => this.conectarLobbyWs(), espera);
        } else {
          this.lobbyWsReconectando = false;
          this.mostrarToast(
            "Lista de salas em atualização manual (a cada 30 s). Puxe a tela para atualizar.",
            false
          );
          this.carregarSalasPublicas();
          pararLobbyHttpFallback();
          const store = this;
          intervaloLobbyHttpFallback = setInterval(() => {
            if (store.view === "inicio") store.carregarSalasPublicas();
          }, 30000);
        }
      };
    },

    fecharDialogs() {
      if (
        this.dialogAberto === "jogar" &&
        this.filaRanqueada &&
        this.filaPodeCancelar
      ) {
        this.pararFilaRanqueada(
          this.filaFase === "conectando" ? { forcar: true } : {}
        );
      }
      this.dialogAberto = null;
      this.dialogAvatarAberto = false;
      this.aviso.aoConfirmar = null;
      this.aviso.aoCancelar = null;
      this.dialogContaForcarRegistro = false;
      this.dialogContaIrDiretoForm = false;
      this.dialogContaNickSugerido = "";
    },

    abrirDialogAvatar() {
      if (!this.conta) return;
      this.dialogAvatarAberto = true;
    },

    fecharDialogAvatar() {
      this.dialogAvatarAberto = false;
    },

    async abrirDialog(nome) {
      const anterior = this.dialogAberto;
      if (
        anterior === "jogar" &&
        this.filaRanqueada &&
        this.filaPodeCancelar &&
        nome !== "jogar"
      ) {
        this.pararFilaRanqueada();
      }
      if (
        (nome === "jogar" || nome === "criarSala") &&
        !(await this.assegurarSemConflitoJogoAtivo())
      ) {
        return;
      }
      if (nome !== "aviso") {
        this.aviso.aoConfirmar = null;
        this.aviso.aoCancelar = null;
      }
      this.dialogAberto = nome;
      if (nome === "jogar") {
        this.carregarRankingRanqueado();
      }
    },

    preencherFormConfigurarSala() {
      const cfg = this.dadosSala?.configuracao || {};
      const min = Math.max(2, this.lobbyJogadores?.length || 2);
      const maxAtual = cfg.maximoJogadores || 4;
      Object.assign(this.formConfigurarSala, {
        minJogadores: min,
        maxJogadores: Math.max(min, maxAtual),
        mesmaPalavra: cfg.mesmaPalavra !== false,
        verOutros: cfg.verOutros !== false,
        modoSessao: cfg.modoSessao || "pontos",
        metaVitorias: cfg.metaVitorias || 5,
        inicioAutoDois: !!cfg.inicioAutoDois,
        tempoLimite: cfg.tempoLimiteSegundos ?? 180,
        temSenhaAtual: !!this.dadosSala?.temSenha,
        senhaNova: "",
        removerSenha: false,
      });
    },

    abrirConfigurarSala() {
      if (!(this.dadosSala?.souCriador ?? this.souCriador)) return;
      if (this.dadosSala?.configuracao?.ranqueada) {
        this.mostrarToast("Duelo ranqueado não permite alterar configuração.", true);
        return;
      }
      if (this.dadosSala?.estadoSala && this.dadosSala.estadoSala !== "aguardando") {
        this.mostrarToast("Só é possível configurar na sala de espera.", true);
        return;
      }
      this.preencherFormConfigurarSala();
      this.abrirDialog("configSala");
    },

    submeterConfigurarSala(ev) {
      ev?.preventDefault?.();
      const c = this.formConfigurarSala;
      if (c.maxJogadores < c.minJogadores) {
        this.mostrarToast(
          `Máximo não pode ser menor que ${c.minJogadores} (pessoas na sala).`,
          true
        );
        return;
      }
      this.wsEnviar("configurar", {
        mesmaPalavra: c.mesmaPalavra,
        verOutros: c.verOutros,
        maximoJogadores: c.maxJogadores,
        tempoLimiteSegundos: c.tempoLimite || 0,
        modoSessao: c.modoSessao,
        metaVitorias: c.metaVitorias,
        inicioAutoDois: c.inicioAutoDois,
        senhaNova: c.removerSenha ? "" : (c.senhaNova || "").trim(),
        removerSenha: !!c.removerSenha,
      });
      this.fecharDialogs();
      this.mostrarToast("Configuração enviada.", false, true);
    },

    definirNick(valor) {
      this.nick = (valor || "Jogador").trim().slice(0, 24) || "Jogador";
      SalvarNickLocal(this.nick);
      this.carregarInfoDiaria();
    },

    prepararNovaRodadaArena() {
      acoesArena.cancelarTimeoutChuteOnline();
      this.arenaTentativas = [];
      this.arenaTentativasExibidas = 0;
      this.tentativa = 0;
      this.letras = LetrasVazias();
      this.indiceCursor = 0;
      this.teclado = {};
      this.carregandoChute = false;
      this.linhaShake = null;
    },

    /** Teclado espelha só as tentativas atuais da rodada (evita cores da rodada anterior). */
    sincronizarTecladoArena(Tentativas) {
      let novo = {};
      (Tentativas || []).forEach((t) => {
        novo = RegistrarLetrasNoTeclado(t, novo);
      });
      this.teclado = novo;
    },

    resetarJogo() {
      PararIntervaloPausa();
      this.pararCronometro();
      this.tentativa = 0;
      this.letras = LetrasVazias();
      this.indiceCursor = 0;
      this.encerrada = false;
      this.teclado = {};
      this.tentativasHist = [];
      this.tabuleiros = null;
      this.gradesMulti = [];
      this.prepararNovaRodadaArena();
      this.arenaRodadaSync = null;
      this.palavraSecreta = null;
      this.limparChat();
      this.mostrarToast("");
    },

    iniciarTelaJogo(label) {
      this.resetarJogo();
      this.labelModo = label;
      this.irParaView("jogo");
    },

    async verResultadoDiaria() {
      if (!this.diariaFeita) return;
      try {
        const info = await api.diariaInfo(this.nickJogo);
        const grade =
          ObterStats().ultimaGrade || info.resultado?.gradeTexto || "";
        if (!grade) {
          this.mostrarToast("Resultado de hoje não encontrado.", true);
          return;
        }
        this.resultado = MontarResultadoUi({
          modo: "diaria",
          venceu: !!info.resultado?.venceu,
          tentativa:
            info.resultado?.tentativasUsadas ||
            ObterStats().ultimaTentativas ||
            0,
          maxTentativas: info.maximoTentativas || 6,
          gradeTexto: grade,
          pontos: info.resultado?.pontos,
          dataDia: info.dataDia,
        });
        this.resultado.titulo = "Seu resultado de hoje";
        this.abrirDialog("resultado");
      } catch {
        const S = ObterStats();
        if (S.ultimaGrade) {
          this.resultado = MontarResultadoUi({
            modo: "diaria",
            venceu: !!S.diariaVenceu,
            tentativa: S.ultimaTentativas || 0,
            maxTentativas: 6,
            gradeTexto: S.ultimaGrade,
            dataDia: S.ultimaDiaria,
          });
          this.resultado.titulo = "Seu resultado de hoje";
          this.abrirDialog("resultado");
        }
      }
    },

    async carregarInfoDiaria() {
      try {
        const D = await api.diariaInfo(this.nickJogo);
        const data = new Date(D.dataDia + "T12:00:00");
        this.diariaBadge = data.toLocaleDateString("pt-BR", {
          day: "numeric",
          month: "short",
        });
        AplicarTempoServidor(D);
        this.diariaDataDia = D.dataDia;
        if (D.jaJogou) {
          this.diariaFeita = true;
          this.diariaBtnTexto = "Já jogou hoje";
          if (D.resultado?.gradeTexto) {
            const S = ObterStats();
            S.ultimaDiaria = D.dataDia;
            S.ultimaGrade = D.resultado.gradeTexto;
            S.diariaVenceu = D.resultado.venceu;
            S.ultimaTentativas = D.resultado.tentativasUsadas;
            SalvarStats(S);
            this.statsLocais = S;
          }
        } else {
          this.diariaFeita = false;
          this.diariaBtnTexto = "Jogar agora";
        }
        this.atualizarStatsUI();
      } catch {
        /* ok */
      }
    },

    atualizarStatsUI() {
      this.statsLocais = ObterStats();
    },

    registrarVitoria(modo, tentativas, venceu) {
      if (modo === "pratica") return;
      const S = ObterStats();
      S.vitorias = (S.vitorias || 0) + (venceu ? 1 : 0);
      S.sequencia = venceu ? (S.sequencia || 0) + 1 : 0;
      if (modo === "diaria") {
        S.ultimaDiaria = this.dataDia || DataDiaServidor() || "";
        S.diariaVenceu = venceu;
        S.ultimaTentativas = tentativas;
      }
      SalvarStats(S);
      this.statsLocais = S;
    },

    selecionarCelula(indice) {
      if (!PodeEditarGradeAtualEstado(this)) return;
      if (indice < 0 || indice >= TAMANHO_PALAVRA) return;
      this.indiceCursor = indice;
      if (this.modo && !EhModoSalaOnline(this.modo) && this.idPartida) {
        this.persistir();
      }
    },

    moverCursorCelula(delta) {
      if (!PodeEditarGradeAtualEstado(this)) return;
      const Novo = this.indiceCursor + delta;
      if (Novo >= 0 && Novo < TAMANHO_PALAVRA) {
        this.selecionarCelula(Novo);
      }
    },

    onTecla(k) {
      if (!PodeEditarGradeAtualEstado(this) || this.carregandoChute) return;
      this.letras = NormalizarLetrasProgresso(this.letras);
      if (k === "back") {
        if (this.letras[this.indiceCursor]) {
          this.letras[this.indiceCursor] = "";
          TocarSom("apagar");
        } else {
          for (let i = this.indiceCursor - 1; i >= 0; i--) {
            if (this.letras[i]) {
              this.letras[i] = "";
              this.indiceCursor = i;
              TocarSom("apagar");
              break;
            }
          }
        }
      } else if (k === "enter") {
        this.enviarChute();
        return;
      } else {
        this.letras[this.indiceCursor] = k;
        TocarSom("tecla");
        const prox = ProximoIndiceVazio(this.letras, this.indiceCursor + 1);
        this.indiceCursor = prox;
      }
      if (this.modo && !EhModoSalaOnline(this.modo) && this.idPartida) {
        this.persistir();
      }
    },

    async enviarChute() {
      if (
        EhModoSalaOnline(this.modo) &&
        this.estadoSalaArena === "entre_rodadas"
      ) {
        return;
      }
      if (!LetrasPreenchidas(this.letras)) {
        this.mostrarToast("Preencha as 5 letras", true);
        return;
      }
      if (EhModoSalaOnline(this.modo)) {
        if (this.carregandoChute) return;
        const palavra = MontarPalavraChute(this.letras);
        const tentativasAnteriores = this.arenaTentativas;
        if (PalavraJaFoiTentada(palavra, tentativasAnteriores)) {
          this.tratarChuteInvalido("Você já tentou essa palavra.");
          return;
        }
        if (this.espectador) {
          this.mostrarToast("Espectadores não chutam.", true);
          return;
        }
        const sock = acoesArena.obterSocketSala();
        if (sock?.readyState === WebSocket.OPEN) {
          this.carregandoChute = true;
          acoesArena.iniciarTimeoutChuteOnline(
            this,
            tentativasAnteriores.length
          );
          sock.send(
            JSON.stringify({
              tipo: "chute",
              dados: { palavra },
            })
          );
          return;
        }
        if (this.codigoSala && this.idJogador) {
          this.conectarWs();
          return acoesArena.enviarChuteOnlineHttp(
            this,
            palavra,
            tentativasAnteriores.length
          );
        }
        this.mostrarToast("Sem conexão com o servidor.", true);
        return;
      }

      if (this.modo === "pratica") {
        return enviarChutePraticaLocal.call(this, cacheDicionarioSet);
      }

      return acoesSolo.enviarChuteSolo.call(this);
    },

    mostrarAviso({
      titulo,
      mensagem,
      dica,
      tipo,
      textoBotao,
      aoConfirmar,
    }) {
      const ehNick = tipo === "nick" || EhErroNick(mensagem);
      this.aviso = {
        titulo,
        mensagem,
        dica: dica || "",
        tipo: ehNick ? "nick" : tipo || "info",
        textoBotao: textoBotao || (ehNick ? "Entrar com outro nick" : "Entendi"),
        textoBotaoSec: "Cancelar",
        nickTemp: this.nickJogo,
        senhaTemp: "",
        conviteCodigo: "",
        aoConfirmar: aoConfirmar || null,
        aoCancelar: null,
      };
      this.abrirDialog("aviso");
    },

    mostrarConfirmacao({
      titulo = "Confirmar",
      mensagem,
      dica,
      textoConfirmar = "Confirmar",
      textoCancelar = "Cancelar",
      aoConfirmar,
      aoCancelar,
    }) {
      this.aviso = {
        titulo,
        mensagem,
        dica: dica || "",
        tipo: "confirm",
        textoBotao: textoConfirmar,
        textoBotaoSec: textoCancelar,
        nickTemp: "",
        senhaTemp: "",
        conviteCodigo: "",
        aoConfirmar: aoConfirmar || null,
        aoCancelar: aoCancelar || null,
      };
      this.abrirDialog("aviso");
    },

    cancelarAviso() {
      const cb = this.aviso.aoCancelar;
      if (this.aviso.tipo === "convite" || this.aviso.tipo === "senhaSala") {
        this.conviteSalaCodigo = "";
      }
      this.fecharDialogs();
      cb?.();
    },

    confirmarAviso() {
      if (this.aviso.tipo === "convite") {
        this.confirmarConviteSala();
        return;
      }
      if (this.aviso.tipo === "senhaSala") {
        this.confirmarSenhaConviteSala();
        return;
      }
      if (this.aviso.tipo === "nick") {
        const novo = this.aviso.nickTemp.trim().slice(0, 24);
        if (!novo) return;
        this.definirNick(novo);
      }
      const cb = this.aviso.aoConfirmar;
      this.fecharDialogs();
      cb?.();
    },

    async submeterCriarSala(ev) {
      if (!(await this.assegurarSemConflitoJogoAtivo())) return;
      ev?.preventDefault?.();
      this.nick = this.nickJogo;
      SalvarNickLocal(this.nick);
      const c = this.formCriarSala;
      try {
        const D = await api.salaCriar({
          nomeJogador: this.nickJogo,
          salaPublica: true,
          mesmaPalavra: c.mesmaPalavra,
          verOutros: c.verOutros,
          maximoJogadores: c.maxJogadores,
          senha: c.senha.trim() || null,
          tempoLimiteSegundos: c.tempoLimite || 0,
          modoSessao: c.modoSessao,
          metaVitorias: c.metaVitorias,
          inicioAutoDois: c.inicioAutoDois,
        });
        this.entrarNaSala(D);
      } catch (e) {
        const msg = e.message || "Erro ao criar sala";
        this.mostrarAviso({
          titulo: EhErroNick(msg) ? "Nick já em uso" : "Não foi possível criar",
          mensagem: EhErroNick(msg)
            ? `O nick «${this.nickJogo}» já está ocupado nesta sala. Escolha outro apelido.`
            : msg,
          dica: EhErroNick(msg)
            ? "Cada jogador precisa de um nick único na mesma sala."
            : undefined,
          tipo: EhErroNick(msg) ? "nick" : "erro",
          aoConfirmar: EhErroNick(msg)
            ? () => this.submeterCriarSala()
            : undefined,
        });
      }
    },

    aplicarCredenciaisPartida(D) {
      if (D?.idPartida) this.idPartida = D.idPartida;
      if (D?.tokenSessao) this.tokenSessao = D.tokenSessao;
    },

    entrarNaSala(D) {
      if (D.configuracao?.ranqueada) {
        this.entrarNaSalaRanqueada(D);
        return;
      }
      LimparSessao();
      this.modo = "arena";
      this.configArena = D.configuracao;
      this.codigoSala = D.codigoSala;
      this.idJogador = D.idJogador;
      this.aplicarCredenciaisPartida(D);
      this.souCriador = D.souCriador;
      this.codigoEntrada = "";
      this.dadosSala = D;
      this.fecharDialogs();
      if (D.estadoSala === "aguardando") {
        this.irParaView("arenaLobby");
      }
      this.conectarWs();
      this.persistir();
    },

    tratarErroEntradaSala(mensagem) {
      const msg = mensagem || "Não foi possível entrar";
      const conflito = EhErroNick(msg);
      const senhaErrada = /senha/i.test(msg);
      this.mostrarAviso({
        titulo: conflito
          ? "Nick já em uso"
          : senhaErrada
            ? "Senha incorreta"
            : "Não foi possível entrar",
        mensagem: conflito
          ? `Alguém na sala já está como «${this.nickJogo}». Troque seu apelido e tente de novo.`
          : msg,
        dica: conflito
          ? "Use um nick diferente do que já está na lista de jogadores."
          : undefined,
        tipo: conflito ? "nick" : "erro",
        aoConfirmar: conflito ? () => this.entrarSala() : undefined,
      });
    },

    async executarEntradaSala(codigoInformado) {
      this.nick = this.nickJogo;
      SalvarNickLocal(this.nick);
      const cod = (codigoInformado || this.codigoEntrada).trim().toUpperCase();
      if (cod.length !== 6) {
        return { ok: false, mensagem: "Código inválido.", codigoInvalido: true };
      }
      this.codigoEntrada = cod;
      try {
        const D = await api.salaEntrar({
          codigoSala: cod,
          nomeJogador: this.nickJogo,
          senha: this.senhaEntrada.trim() || null,
          espectador: this.espectadorEntrada,
        });
        this.entrarNaSala(D);
        TocarSom("entrada");
        if (
          D.estadoSala === "jogando" ||
          D.estadoSala === "entre_rodadas" ||
          D.estadoSala === "countdown" ||
          this.espectadorEntrada
        ) {
          this.espectador = this.espectadorEntrada;
          if (this.espectadorEntrada) {
            this.irParaView("jogo");
          } else if (D.estadoSala === "jogando") {
            this.iniciarTelaJogo("Arena");
          } else {
            this.irParaView("jogo");
          }
        }
        this.atualizarArena(D);
        this.conviteSalaCodigo = "";
        return { ok: true };
      } catch (e) {
        const msg = e.message || "Não foi possível entrar";
        return {
          ok: false,
          mensagem: msg,
          precisaSenha: /senha/i.test(msg),
        };
      }
    },

    async entrarSala() {
      if (!(await this.assegurarSemConflitoJogoAtivo())) return;
      const cod = this.codigoEntrada.trim().toUpperCase();
      if (cod.length !== 6) {
        this.mostrarAviso({
          titulo: "Código inválido",
          mensagem: "Digite as 6 letras do código da sala para entrar.",
          dica: "O código aparece na tela de quem criou a sala.",
        });
        return;
      }
      const R = await this.executarEntradaSala(cod);
      if (R.ok) return;
      if (R.precisaSenha) {
        this.mostrarAvisoSenhaConviteSala(cod);
        return;
      }
      this.tratarErroEntradaSala(R.mensagem);
    },

    entrarSalaListaPublica(codigo, temSenha = false) {
      const cod = (codigo || "").trim().toUpperCase();
      if (cod.length !== 6) return;
      this.codigoEntrada = cod;
      if (temSenha) {
        this.mostrarAvisoSenhaConviteSala(cod);
        return;
      }
      this.entrarSala();
    },

    limparQuerySala() {
      const u = new URL(location.href);
      if (!u.searchParams.has("sala")) return;
      u.searchParams.delete("sala");
      const destino = u.pathname + u.search + u.hash;
      history.replaceState({}, "", destino || "/");
    },

    codigoSalaDaUrl() {
      const cod = new URLSearchParams(location.search).get("sala");
      if (!cod) return "";
      const normalizado = cod.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
      return normalizado.length === 6 ? normalizado : "";
    },

    mostrarAvisoConviteSala(codigo, temSenha) {
      this.aviso = {
        titulo: `Entrar na sala ${codigo}`,
        mensagem: temSenha
          ? "Informe seu nick e a senha da sala para entrar."
          : "Escolha um nick e você entra direto na sala de espera.",
        dica: "Conta com e-mail é opcional — visitante basta para jogar na arena.",
        tipo: "convite",
        textoBotao: "Entrar na sala",
        textoBotaoSec: "Cancelar",
        nickTemp: NormalizarNick(this.nickJogo) || "",
        senhaTemp: "",
        conviteCodigo: codigo,
        exigeSenha: !!temSenha,
        aoConfirmar: null,
        aoCancelar: null,
      };
      this.abrirDialog("aviso");
    },

    mostrarAvisoSenhaConviteSala(codigo) {
      this.aviso = {
        titulo: `Sala ${codigo}`,
        mensagem: "Esta sala está protegida por senha.",
        dica: "",
        tipo: "senhaSala",
        textoBotao: "Entrar",
        textoBotaoSec: "Cancelar",
        nickTemp: "",
        senhaTemp: this.senhaEntrada || "",
        conviteCodigo: codigo,
        exigeSenha: true,
        aoConfirmar: null,
        aoCancelar: null,
      };
      this.abrirDialog("aviso");
    },

    async confirmarConviteSala() {
      const codigo = this.aviso.conviteCodigo;
      const senha = (this.aviso.senhaTemp || "").trim();
      if (!this.conta) {
        const V = ValidarNick(this.aviso.nickTemp);
        if (!V.ok) {
          this.mostrarToast(V.mensagem, true);
          return;
        }
        const auth = await this.authVisitante(V.nick);
        if (auth?.ok === false) return;
      }
      this.fecharDialogs();
      this.senhaEntrada = senha;
      this.espectadorEntrada = false;
      const R = await this.executarEntradaSala(codigo);
      if (R.ok) return;
      if (R.precisaSenha) {
        this.mostrarAvisoSenhaConviteSala(codigo);
        return;
      }
      this.tratarErroEntradaSala(R.mensagem);
    },

    async confirmarSenhaConviteSala() {
      const codigo = this.aviso.conviteCodigo;
      const senha = (this.aviso.senhaTemp || "").trim();
      if (!senha) {
        this.mostrarToast("Informe a senha da sala.", true);
        return;
      }
      this.fecharDialogs();
      this.senhaEntrada = senha;
      this.espectadorEntrada = false;
      const R = await this.executarEntradaSala(codigo);
      if (R.ok) return;
      if (R.precisaSenha) {
        this.mostrarAvisoSenhaConviteSala(codigo);
        return;
      }
      this.tratarErroEntradaSala(R.mensagem);
    },

    async tentarEntrarConviteAutomatico(codigo) {
      this.espectadorEntrada = false;
      const R = await this.executarEntradaSala(codigo);
      if (R.ok) return true;
      if (R.precisaSenha) {
        this.mostrarAvisoSenhaConviteSala(codigo);
        return false;
      }
      this.tratarErroEntradaSala(R.mensagem);
      return false;
    },

    capturarConviteSalaDaUrl() {
      const cod = this.codigoSalaDaUrl();
      if (cod) this.conviteSalaCodigo = cod;
      return this.conviteSalaCodigo || "";
    },

    limparConviteSalaPendente() {
      this.conviteSalaCodigo = "";
    },

    async processarConviteAposBoot(retomou) {
      const codigo = this.capturarConviteSalaDaUrl();
      if (!codigo) return;
      if (retomou && CodigoConviteConflita(this, codigo)) {
        return new Promise((resolve) => {
          this.mostrarConfirmacao({
            titulo: "Sair da partida atual?",
            mensagem: `Você retomou uma partida em andamento. Para entrar na sala ${codigo.toUpperCase()}, é preciso sair da partida atual.`,
            dica: "Se cancelar, o link de convite será ignorado nesta visita.",
            textoConfirmar: "Sair e entrar na sala",
            textoCancelar: "Continuar jogando",
            aoConfirmar: async () => {
              await this.voltarInicio();
              await this.processarConviteSala();
              resolve();
            },
            aoCancelar: () => {
              this.limparConviteSalaPendente();
              this.limparQuerySala();
              resolve();
            },
          });
        });
      }
      await this.processarConviteSala();
    },

    async processarConviteSala() {
      if (this.processandoConviteSala) return;

      const codigo = (this.conviteSalaCodigo || this.codigoSalaDaUrl()).trim();
      if (!codigo) {
        if (new URLSearchParams(location.search).get("sala")) {
          this.mostrarToast("Código de sala inválido no link.", true);
          this.limparQuerySala();
        }
        this.limparConviteSalaPendente();
        return;
      }

      this.conviteSalaCodigo = codigo.toUpperCase();
      this.processandoConviteSala = true;
      this.mostrarTutorial = false;
      this.limparQuerySala();

      if (
        this.codigoSala &&
        this.codigoSala !== codigo &&
        this.idJogador &&
        EhModoSalaOnline(this.modo)
      ) {
        await this.voltarInicio();
      }

      if (this.codigoSala === codigo && this.idJogador) {
        if (this.view !== "arenaLobby" && this.view !== "jogo") {
          this.irParaView(
            this.modo === "ranqueada" ? "inicio" : "arenaLobby"
          );
        }
        return;
      }

      try {
        let info;
        try {
          info = await api.salaConvite(codigo);
        } catch {
          this.mostrarToast("Sala não encontrada.", true);
          this.irParaView("inicio");
          this.limparConviteSalaPendente();
          return;
        }

        if (info.partidaEncerrada) {
          this.mostrarToast("Esta sala já encerrou a partida.", true);
          this.irParaView("inicio");
          this.limparConviteSalaPendente();
          return;
        }

        if (info.cheia) {
          this.mostrarToast(
            `Sala cheia (${info.jogadoresAtivos}/${info.maximoJogadores} jogadores).`,
            true
          );
          this.irParaView("inicio");
          this.limparConviteSalaPendente();
          return;
        }

        this.codigoEntrada = codigo;

        if (this.conta) {
          if (info.temSenha && !this.senhaEntrada.trim()) {
            this.mostrarAvisoSenhaConviteSala(codigo);
            return;
          }
          await this.tentarEntrarConviteAutomatico(codigo);
          return;
        }

        this.mostrarAvisoConviteSala(codigo, info.temSenha);
      } finally {
        this.processandoConviteSala = false;
      }
    },

    pararSyncArena() {
      acoesArena.pararSyncArena();
    },

    sincronizarArenaHttp() {
      return acoesArena.sincronizarArenaHttp(this);
    },

    iniciarSyncArena() {
      acoesArena.iniciarSyncArena(this);
    },

    conectarWs() {
      acoesArena.conectarWsArena(this);
    },

    processarWs(M) {
      acoesArena.processarWsArena(this, M);
    },

    alternarProntoLobby() {
      const eu = this.lobbyJogadores.find((j) => j.souEu);
      this.wsEnviar("pronto", { pronto: !eu?.pronto });
    },

    expulsarJogadorLobby(idJogador) {
      if (!idJogador || idJogador === this.idJogador) return;
      this.wsEnviar("expulsar", { idJogador });
    },

    wsEnviar(tipo, dados = {}) {
      acoesArena.wsEnviar(tipo, dados);
    },

    AplicarToastInstigacaoSerie(D) {
      if (!this.porVitoriasArena || this.espectador || !D?.placar?.length) {
        this.ultimaInstigacaoSerieChave = null;
        return;
      }
      if (D.partidaEncerrada) {
        this.ultimaInstigacaoSerieChave = null;
        return;
      }
      const Estado = D.estadoSala;
      if (
        Estado !== "jogando" &&
        Estado !== "countdown" &&
        Estado !== "entre_rodadas"
      ) {
        return;
      }
      const Eu = D.placar.find((j) => j.idJogador === this.idJogador);
      const Opp = D.placar.find((j) => j.idJogador !== this.idJogador);
      if (!Eu || !Opp) return;
      const Inst = CalcularInstigacaoSerie({
        vitoriasEu: Eu.vitoriasRodada || 0,
        vitoriasOpp: Opp.vitoriasRodada || 0,
        meta: this.metaVitoriasArena,
      });
      const Chave = ChaveInstigacaoSerie(
        Inst,
        Eu.vitoriasRodada || 0,
        Opp.vitoriasRodada || 0
      );
      if (!Chave) {
        this.ultimaInstigacaoSerieChave = null;
        return;
      }
      if (Chave === this.ultimaInstigacaoSerieChave) return;
      this.ultimaInstigacaoSerieChave = Chave;
      this.mostrarToast(Inst.texto, false, true);
    },

    atualizarArena(D, Opcoes = {}) {
      const eu = D.jogadores?.find((j) => j.souEu);
      if (
        this.idJogador &&
        D.estadoSala === "aguardando" &&
        !eu &&
        (this.view === "arenaLobby" || this.view === "inicio")
      ) {
        this.mostrarToast("Você foi removido da sala.", true);
        this.voltarInicio();
        return;
      }
      this.configArena = D.configuracao;
      const estadoAnterior = this.estadoSalaArena;
      this.estadoSalaArena = D.estadoSala;
      this.dadosSala = D;
      this.espectador = !!eu?.espectador;
      this.souCriador = D.souCriador ?? this.souCriador;
      this.AplicarToastInstigacaoSerie(D);

      const labelJogo =
        this.modo === "ranqueada" ? "Ranqueado" : "Arena";
      const lobbyView =
        this.modo === "ranqueada" ? "inicio" : "arenaLobby";

      if (D.estadoSala === "aguardando") {
        this.irParaView(lobbyView);
      } else if (this.view === lobbyView || this.view === "arenaLobby") {
        /* mantém jogo se já em jogo */
      }

      if (
        (D.estadoSala === "jogando" ||
          D.estadoSala === "entre_rodadas" ||
          D.estadoSala === "countdown") &&
        this.view !== "jogo"
      ) {
        if (this.espectador) {
          this.irParaView("jogo");
        } else {
          this.iniciarTelaJogo(labelJogo);
        }
      } else if (
        (this.view === "jogo" || this.espectador) &&
        EhModoSalaOnline(this.modo)
      ) {
        this.irParaView("jogo");
      }

      if (eu?.tempoFimEpoch && D.estadoSala === "jogando" && !D.partidaEncerrada) {
        this.iniciarCronometro(eu.tempoFimEpoch);
      } else if (D.estadoSala !== "jogando") {
        this.pararCronometro();
      }

      if (D.rodadaAtual !== this.arenaRodadaSync) {
        this.arenaRodadaSync = D.rodadaAtual;
        this.prepararNovaRodadaArena();
        this.ultimoToastRodadaFim = null;
        if (D.estadoSala === "jogando" && eu && !eu.finalizou) {
          this.encerrada = false;
        }
      }

      if (D.estadoSala === "jogando" && estadoAnterior !== "jogando") {
        this.prepararNovaRodadaArena();
        if (eu && !eu.finalizou) {
          this.encerrada = false;
        }
      }

      if (
        eu &&
        !this.espectador &&
        this.view === "jogo" &&
        D.estadoSala === "jogando"
      ) {
        const total = eu.tentativas?.length || 0;
        const linhaNova = total > this.arenaTentativasExibidas;
        this.arenaTentativas = (eu.tentativas || []).map((t, i) => {
          const norm = NormalizarTentativa(t);
          if (linhaNova && i === total - 1) {
            const comAnim = { ...norm, animar: true };
            AgendarFimAnimacao(comAnim);
            return comAnim;
          }
          return norm;
        });
        this.sincronizarTecladoArena(eu.tentativas);
        this.tentativa = total;
        this.arenaTentativasExibidas = total;
        this.encerrada = !!eu.finalizou;
        if (linhaNova) {
          acoesArena.cancelarTimeoutChuteOnline();
          this.carregandoChute = false;
          this.letras = LetrasVazias();
          this.indiceCursor = 0;
        }
        if (linhaNova && total > 0) {
          const ultima = eu.tentativas[total - 1];
          if (ultima?.venceu) TocarSom("acerto");
          else TocarSom("chute");
        }
      } else if (
        eu &&
        this.view === "jogo" &&
        D.estadoSala === "entre_rodadas"
      ) {
        this.encerrada = true;
        this.teclado = {};
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
        this.tentativa = 0;
        this.arenaTentativas = [];
        this.arenaTentativasExibidas = 0;
      } else if (this.view === "jogo" && D.estadoSala === "countdown") {
        this.encerrada = true;
        this.teclado = {};
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
        this.tentativa = 0;
        this.arenaTentativas = [];
        this.arenaTentativasExibidas = 0;
      } else if (this.view === "jogo" && D.estadoSala === "pausada") {
        this.encerrada = true;
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
      }

      if (
        EhModoSalaOnline(this.modo) &&
        this.view === "jogo" &&
        !this.espectador &&
        D.estadoSala === "jogando"
      ) {
        const jogador = D.jogadores?.find((j) => j.souEu);
        if (jogador && !jogador.finalizou) {
          this.encerrada = false;
        }
      }

      this.renderizarChat(D);
      this.atualizarEntreRodadas(D);

      PararIntervaloCountdown();
      if (
        this.view === "jogo" &&
        D.estadoSala === "countdown" &&
        D.countdownSegundos != null &&
        D.countdownSegundos > 0
      ) {
        this.countdownSegundos = D.countdownSegundos;
        intervaloCountdown = setInterval(() => {
          if (this.countdownSegundos > 1) {
            this.countdownSegundos -= 1;
            return;
          }
          PararIntervaloCountdown();
          this.countdownSegundos = null;
          if (this.dadosSala?.estadoSala === "countdown") {
            acoesArena.sincronizarArenaHttp(this);
          }
        }, 1000);
      } else {
        this.countdownSegundos = null;
      }

      PararIntervaloPausa();
      if (
        this.view === "jogo" &&
        (D.estadoSala === "pausada" || D.pausada) &&
        D.segundosPausaRestantes != null &&
        D.segundosPausaRestantes > 0
      ) {
        intervaloPausa = setInterval(() => {
          const Sala = this.dadosSala;
          if (!Sala || Sala.estadoSala !== "pausada") {
            PararIntervaloPausa();
            return;
          }
          const Restante = Sala.segundosPausaRestantes;
          if (Restante == null || Restante <= 1) {
            PararIntervaloPausa();
            acoesArena.sincronizarArenaHttp(this);
            return;
          }
          Sala.segundosPausaRestantes = Restante - 1;
        }, 1000);
      }

      this.ultimoVencedorRodadaId = D.ultimoVencedorRodadaId;
      if (
        D.estadoSala === "entre_rodadas" &&
        D.rodadaAtual != null &&
        D.rodadaAtual !== this.ultimoToastRodadaFim
      ) {
        this.ultimoToastRodadaFim = D.rodadaAtual;
        const msg = D.mensagemFimRodada;
        if (msg) {
          this.toastVitoriaRodada = msg;
          const ids = D.vencedoresRodadaIds || [];
          const euVenceu =
            D.ultimoVencedorRodadaId === this.idJogador ||
            ids.includes(this.idJogador);
          if (euVenceu) TocarSom("vitoria");
          setTimeout(() => {
            this.toastVitoriaRodada = "";
          }, 4500);
        }
      }

      if (D.progressoEvento) {
        this.aplicarProgressoResposta(D.progressoEvento);
      }

      if (!D.partidaEncerrada) {
        this.persistir();
      }

      if (D.partidaEncerrada) {
        this.pararCronometro();
        this.encerrada = true;
        const ehArena = this.modo === "arena";
        const exibirResultado = Opcoes.exibirResultadoEncerrada !== false;

        if (ehArena && !D.partidaCancelada) {
          this.irParaView("arenaLobby");
          LimparSessao();
          if (this.conta?.idConta && !this.conta?.ehVisitante) {
            api.contaLimparJogoAtivo().catch(() => {});
          }
          this.jogoAtivo = null;
          if (exibirResultado) {
            const campeao = D.placar?.[0];
            const venci = D.vencedorId === this.idJogador;
            const IdPartida = D.idPartida || this.idPartida;
            if (IdPartida && this.ultimaPartidaResultadoExibida !== IdPartida) {
              this.ultimaPartidaResultadoExibida = IdPartida;
              setTimeout(
                () => this.mostrarResultadoArena(D, venci, campeao),
                300
              );
            }
          }
        } else {
          acoesArena.fecharSocketSala();
          this.irParaView("inicio");
          LimparSessao();
          if (D.partidaCancelada) {
            this.mostrarToast("Partida encerrada — nada foi registrado.");
          } else if (exibirResultado) {
            const campeao = D.placar?.[0];
            const venci = D.vencedorId === this.idJogador;
            const IdPartida = D.idPartida || this.idPartida;
            if (IdPartida && this.ultimaPartidaResultadoExibida !== IdPartida) {
              this.ultimaPartidaResultadoExibida = IdPartida;
              setTimeout(
                () => this.mostrarResultadoArena(D, venci, campeao),
                300
              );
            }
          }
          if (this.modo === "ranqueada") {
            this.modo = null;
            this.codigoSala = null;
            this.idJogador = null;
            this.dadosSala = null;
          }
        }
      } else if (
        this.modo === "arena" &&
        D.estadoSala === "aguardando" &&
        !D.partidaEncerrada
      ) {
        this.ultimaPartidaResultadoExibida = null;
      }
    },

    atualizarEntreRodadas(D) {
      if (D.estadoSala !== "entre_rodadas" || D.partidaEncerrada) return;
      const lider = D.placar?.[0];
      const meta = this.metaVitoriasArena;
      if (!lider) return;
      /* texto exibido no componente via getter */
    },

    limparChat() {
      timersChat.forEach((t) => clearTimeout(t));
      timersChat = new Map();
      chavesChatVistas.clear();
      this.chatMensagens = [];
      if (timerBalaoFala) {
        clearTimeout(timerBalaoFala);
        timerBalaoFala = null;
      }
      this.balaoFala = null;
    },

    _ExibirBalaoFala(M, chave) {
      if (timerBalaoFala) clearTimeout(timerBalaoFala);
      this.balaoFala = {
        chave,
        idJogador: M.idJogador,
        nomeJogador: M.nomeJogador,
        texto: M.texto,
        saindo: false,
      };
      timerBalaoFala = setTimeout(() => {
        if (this.balaoFala?.chave === chave) {
          this.balaoFala = { ...this.balaoFala, saindo: true };
          setTimeout(() => {
            if (this.balaoFala?.chave === chave) this.balaoFala = null;
          }, BALAO_FALA_SAIDA_MS);
        }
        timerBalaoFala = null;
      }, BALAO_FALA_MS);
    },

    renderizarChat(D) {
      const msgs = D.mensagensChat || [];
      for (const M of msgs) {
        const chave = ChaveMsgChat(M);
        if (chavesChatVistas.has(chave)) continue;
        chavesChatVistas.add(chave);
        const item = {
          chave,
          nomeJogador: M.nomeJogador,
          texto: M.texto,
          saindo: false,
        };
        if (M.idJogador && M.idJogador !== this.idJogador) {
          TocarSom("chat");
        }
        this.chatMensagens.push(item);
        const balaoProprioJaVisivel =
          this.balaoFala &&
          M.idJogador === this.idJogador &&
          this.balaoFala.idJogador === M.idJogador &&
          this.balaoFala.texto === M.texto;
        if (!balaoProprioJaVisivel) {
          this._ExibirBalaoFala(M, chave);
        }
        const timer = setTimeout(() => {
          const idx = this.chatMensagens.findIndex((x) => x.chave === chave);
          if (idx >= 0) {
            this.chatMensagens[idx].saindo = true;
            setTimeout(() => {
              this.chatMensagens = this.chatMensagens.filter(
                (x) => x.chave !== chave
              );
            }, 500);
          }
          timersChat.delete(chave);
        }, CHAT_VIDA_MS);
        timersChat.set(chave, timer);
        const visiveis = this.chatMensagens.filter((x) => !x.saindo);
        while (visiveis.length > CHAT_MAX_VISIVEIS) {
          const velho = visiveis.shift();
          const t = timersChat.get(velho.chave);
          if (t) clearTimeout(t);
          velho.saindo = true;
          setTimeout(() => {
            this.chatMensagens = this.chatMensagens.filter(
              (x) => x.chave !== velho.chave
            );
          }, 500);
        }
      }
    },

    enviarChatFrase(texto) {
      if (!this.podeEnviarChatRapido) {
        this.mostrarToast("Aguarde o balão sumir para falar de novo.");
        return;
      }
      const chave = `opt|${this.idJogador}|${texto}|${Date.now()}`;
      this._ExibirBalaoFala(
        {
          idJogador: this.idJogador,
          nomeJogador: this.nickJogo,
          texto,
        },
        chave
      );
      this.wsEnviar("chat", { texto });
    },

    pararCronometro() {
      if (intervaloTimer) {
        clearInterval(intervaloTimer);
        intervaloTimer = null;
      }
      this.cronometroVisivel = false;
      this.cronometroUrgente = false;
    },

    tickCronometro(tempoFimEpoch) {
      const restante = Math.ceil(tempoFimEpoch - Date.now() / 1000);
      this.cronometroVisivel = true;
      this.cronometroTexto = FormatarCronometro(restante);
      this.cronometroUrgente = restante <= 15;
      if (restante <= 0) {
        this.pararCronometro();
        this.cronometroTexto = "0:00";
      }
    },

    iniciarCronometro(tempoFimEpoch) {
      this.pararCronometro();
      if (!tempoFimEpoch) return;
      this.tickCronometro(tempoFimEpoch);
      intervaloTimer = setInterval(
        () => this.tickCronometro(tempoFimEpoch),
        250
      );
    },

    fecharSocketSala() {
      this.pararSyncArena();
      acoesArena.fecharSocketSala();
      this.wsUrl = null;
      this.wsConectado = false;
      this.bannerReconexao = false;
      this.tentativasReconexao = 0;
    },

    async sairDaSala(codigoSala = this.codigoSala, idJogador = this.idJogador) {
      if (codigoSala && idJogador) {
        try {
          await api.salaSair({
            codigoSala,
            idJogador,
          });
        } catch {
          /* ok */
        }
      }
      this.fecharSocketSala();
      LimparSessao();
    },

    mostrarDialogoRetomadaRanqueada(D) {
      const pausada = D.estadoSala === "pausada" || D.pausada;
      const seg = D.segundosPausaRestantes;
      this.mostrarConfirmacao({
        titulo: pausada ? "Duelo ranqueado pausado" : "Duelo ranqueado em andamento",
        mensagem: pausada
          ? seg != null
            ? `A partida está pausada. Você tem cerca de ${seg}s para voltar antes do resultado por abandono.`
            : "A partida está pausada aguardando reconexão."
          : "Você tem uma partida ranqueada ativa. Continue o duelo ou desista para sair.",
        dica: "O código da sala continua o mesmo na tela (ex.: GMVXGJ).",
        textoConfirmar: "Continuar duelo",
        textoCancelar: "Desistir",
        aoConfirmar: () => {},
        aoCancelar: () => this.desistirPartida(),
      });
    },

    async desistirPartida() {
      if (!EhModoSalaOnline(this.modo) || !this.idPartida || !this.idJogador) {
        await this.voltarInicio();
        return;
      }
      if (!this.tokenSessao) {
        this.mostrarToast("Sessão sem token — saia e entre de novo na sala.", true);
        return;
      }
      try {
        const eraRanq = this.modo === "ranqueada";
        const idJogadorLocal = this.idJogador;
        const Resposta = await api.partidaDesistir(this.idPartida, {
          idJogador: this.idJogador,
          tokenSessao: this.tokenSessao,
        });
        const Estado = Resposta?.estado;
        const SemRegistro =
          Resposta?.semPenalidade || Resposta?.partidaCancelada;
        this.fecharSocketSala();
        LimparSessao();
        this.modo = null;
        this.codigoSala = null;
        this.idJogador = null;
        this.idPartida = null;
        this.tokenSessao = null;
        this.dadosSala = null;
        this.estadoSalaArena = null;
        this.irParaView("inicio");
        if (
          eraRanq &&
          Estado?.partidaEncerrada &&
          !SemRegistro &&
          Estado.idPartida
        ) {
          this.modo = "ranqueada";
          const venci = Estado.vencedorId === idJogadorLocal;
          const campeao = Estado.placar?.[0];
          if (this.ultimaPartidaResultadoExibida !== Estado.idPartida) {
            this.ultimaPartidaResultadoExibida = Estado.idPartida;
            setTimeout(() => {
              this.mostrarResultadoArena(Estado, venci, campeao);
              this.modo = null;
            }, 300);
          }
        } else {
          this.mostrarToast(
            SemRegistro
              ? "Você saiu da partida. Nada foi registrado no histórico."
              : "Você desistiu da partida."
          );
        }
        if (this.conta?.idConta && !this.conta?.ehVisitante) {
          await api.contaLimparJogoAtivo().catch(() => {});
        }
        await this.carregarJogoAtivo();
      } catch (e) {
        this.mostrarToast(e.message || "Não foi possível desistir", true);
      }
    },

    async voltarInicio() {
      if (this.partidaRanqueadaAtiva || this.partidaArenaEmRodada) {
        await this.desistirPartida();
        return;
      }
      if (
        this.view === "jogo" &&
        EhModoSalaOnline(this.modo) &&
        !this.espectador &&
        this.idPartida &&
        this.idJogador &&
        !this.dadosSala?.partidaEncerrada
      ) {
        await this.desistirPartida();
        return;
      }
      PararIntervaloPausa();
      this.pararFilaRanqueada();
      this.pararCronometro();
      this.limparChat();
      this.fecharDialogs();
      const eraOnline = EhModoSalaOnline(this.modo);
      const codigo = this.codigoSala;
      const idJ = this.idJogador;
      this.modo = null;
      this.codigoSala = null;
      this.idJogador = null;
      this.idPartida = null;
      this.tokenPartida = null;
      this.tokenSessao = null;
      this.dadosSala = null;
      this.configArena = null;
      this.estadoSalaArena = null;
      this.encerrada = false;
      this.bannerReconexao = false;
      this.souCriador = false;
      this.espectador = false;
      if (eraOnline && codigo && idJ) {
        await this.sairDaSala(codigo, idJ);
      } else {
        this.fecharSocketSala();
        LimparSessao();
      }
      this.irParaView("inicio");
    },

    async retomarSessao() {
      return SolicitarRetomarSessao(() => this.retomarSessaoInterno());
    },

    async retomarSessaoInterno() {
      const salvo = ObterSessao();
      if (!salvo) return false;
      let retomou = false;

      const retomarSala = async (chave, modo, viewLobby, label) => {
        const S = salvo[chave];
        if (!S) return { ok: false, invalida: false };
        try {
          let D;
          if (S.idPartida && (S.tokenSessao || this.conta?.idConta)) {
            D = await api.partidaRetomar(
              S.idPartida,
              S.tokenSessao,
              S.idJogador
            );
          } else {
            D = await api.salaEstado(S.codigoSala, S.idJogador);
          }
          if (D.partidaEncerrada || D.somenteResultado) {
            if (modo === "ranqueada") {
              entrarNaSalaRanqueada.call(this, { ...S, ...D }, S, {
                exibirResultadoEncerrada: true,
              });
            } else {
              this.modo = modo;
              this.codigoSala = S.codigoSala;
              this.idJogador = S.idJogador;
              this.aplicarCredenciaisPartida({ ...S, ...D });
              this.dadosSala = D;
              this.fecharDialogs();
              this.irParaView("arenaLobby");
              this.atualizarArena(D, { exibirResultadoEncerrada: true });
            }
            if (this.conta?.idConta && !this.conta?.ehVisitante) {
              await api.contaLimparJogoAtivo().catch(() => {});
            }
            LimparSessao();
            this.jogoAtivo = null;
            return { ok: true, invalida: false };
          }
          if (D.podeRetomar === false) {
            LimparSessao();
            const msg = D.voceGanhou
              ? "Esta partida já terminou — você venceu."
              : D.vocePerdeu
                ? "Esta partida já terminou — você perdeu."
                : "Esta partida já foi encerrada.";
            this.mostrarToast(msg, !D.voceGanhou);
            return { ok: false, invalida: true };
          }
          this.modo = modo;
          this.codigoSala = S.codigoSala;
          this.idJogador = S.idJogador;
          this.aplicarCredenciaisPartida({ ...S, ...D });
          this.souCriador = D.souCriador;
          this.configArena = D.configuracao;
          this.codigoEntrada = "";
          this.dadosSala = D;
          const emPartida =
            D.estadoSala === "jogando" ||
            D.estadoSala === "entre_rodadas" ||
            D.estadoSala === "countdown" ||
            D.estadoSala === "pausada";
          if (emPartida || S.view === "jogo") {
            this.iniciarTelaJogo(label);
            this.atualizarArena(D);
          } else {
            this.irParaView(viewLobby);
          }
          this.conectarWs();
          this.persistir();
          if (modo === "ranqueada" && emPartida) {
            this.mostrarDialogoRetomadaRanqueada(D);
          } else {
            this.mostrarToast(
              modo === "ranqueada"
                ? "Ranqueado retomado — duelo em andamento"
                : "Arena retomada — você voltou à sala"
            );
          }
          return { ok: true, invalida: false };
        } catch (e) {
          const invalida = e?.status === 404 || e?.status === 410;
          return {
            ok: false,
            invalida,
            erro: e?.message || "Não foi possível retomar a partida.",
          };
        }
      };

      const tratarFalhaRetomar = (resultado) => {
        if (resultado?.ok) return;
        if (resultado?.invalida) {
          const s = ObterSessao();
          if (s?.solo) {
            localStorage.setItem("termoSessao", JSON.stringify({ solo: s.solo }));
          } else {
            LimparSessao();
          }
          return;
        }
        this.mostrarToast(
          resultado?.erro ||
            "Não foi possível retomar — verifique a conexão e toque em Reconectar no início.",
          true
        );
      };

      if (salvo.ranqueada) {
        const R = await retomarSala("ranqueada", "ranqueada", "inicio", "Ranqueado");
        retomou = !!R.ok;
        tratarFalhaRetomar(R);
      }

      if (!retomou && salvo.arena) {
        const R = await retomarSala("arena", "arena", "arenaLobby", "Arena");
        retomou = !!R.ok;
        tratarFalhaRetomar(R);
      }

      if (salvo.solo && !retomou) {
        if (salvo.solo.modo === "pratica" && salvo.solo.palavraSecreta) {
          if (restaurarPraticaLocal.call(this, salvo.solo)) {
            this.persistir();
            this.mostrarToast("Prática retomada de onde você parou");
            return true;
          }
          LimparSessao();
          return false;
        }
        if (salvo.solo.modo === "diaria") {
          try {
            const info = await api.diariaInfo(this.nickJogo);
            AplicarTempoServidor(info);
            if (info.jaJogou) {
              LimparSessao();
              return false;
            }
          } catch {
            /* segue para jogarEstado */
          }
        }
        try {
          const D = await api.jogarEstado(
            salvo.solo.idPartida,
            salvo.solo.tokenPartida
          );
          if (D.encerrada) throw new Error("fim");
          this.modo = D.modo;
          this.idPartida = D.idPartida;
          this.tokenPartida = D.tokenPartida || salvo.solo.tokenPartida;
          this.dataDia = D.dataDia;
          const labels = {
            diaria: "Palavra do dia",
            pratica: "Prática",
            dueto: "Dueto",
            quarteto: "Quarteto",
            desafio: "Desafio",
          };
          this.iniciarTelaJogo(labels[D.modo] || D.modo);
          this.restaurarPartidaSolo(D, salvo.solo);
          this.persistir();
          this.mostrarToast("Partida retomada de onde você parou");
          retomou = true;
        } catch {
          LimparSessao();
        }
      }
      return retomou;
    },

    async carregarSalasPublicas() {
      try {
        const D = await api.salasPublicas();
        this.salasPublicas = D.salas || [];
      } catch (e) {
        this.salasPublicas = [];
        if (e?.status === 503 || e?.status === 429) {
          this.mostrarToast(e.message, true);
        }
      }
    },

    async carregarHomePainel() {
      this.carregandoHome = true;
      try {
        await Promise.all([
          this.carregarSalasPublicas(),
          this.carregarJogoAtivo(),
        ]);
      } finally {
        this.carregandoHome = false;
      }
    },

    voltarMeuPerfil() {
      this.perfilVisualizacao = "eu";
      this.perfilOutro = null;
    },

    async buscarPerfilJogador(nick) {
      const N = (nick || "").trim();
      if (!N) {
        this.mostrarToast("Informe um nick para buscar.", true);
        return;
      }
      if (N.toLowerCase() === (this.nickJogo || "").toLowerCase()) {
        this.voltarMeuPerfil();
        return;
      }
      this.carregandoPerfilOutro = true;
      try {
        const D = await api.jogadorPerfil(N);
        this.perfilOutro = D;
        this.perfilVisualizacao = "outro";
      } catch (Erro) {
        this.mostrarToast(Erro.message || "Jogador não encontrado.", true);
      } finally {
        this.carregandoPerfilOutro = false;
      }
    },

    async abrirPerfil() {
      if (!this.exigirContaRegistrada()) return;
      this.perfilVisualizacao = "eu";
      this.perfilOutro = null;
      this.abrirDialog("perfil");
      this.atualizarStatsUI();
      this.carregandoPerfil = true;
      try {
        await Promise.all([
          api
            .progressoEu()
            .then((p) => {
              if (this.conta) {
                this.conta = { ...this.conta, progresso: p };
                SalvarAuthLocal(this.token, this.conta);
              }
            })
            .catch(() => {}),
          this.carregarRankingRanqueado(),
          this.carregarHistoricoRanqueado(),
          api
            .stats(this.nickJogo)
            .then((d) => {
              this.statsServidor = d;
            })
            .catch(() => {}),
          api
            .historicoDiaria()
            .then((d) => {
              this.historicoDiaria = d.historico || [];
            })
            .catch(() => {
              this.historicoDiaria = [];
            }),
        ]);
      } finally {
        this.carregandoPerfil = false;
      }
    },

    async carregarFrasesChat() {
      try {
        const D = await api.frasesChat();
        this.frasesChat = D.frases || [];
      } catch {
        this.frasesChat = [];
      }
    },

    aplicarQueryDesafio() {
      const d = new URLSearchParams(location.search).get("desafio");
      if (!d) return;
      const cod = d.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
      if (cod.length === 6) {
        this.conviteSalaCodigo = cod;
      } else {
        this.codigoDesafio = cod;
      }
    },

    definirPreferenciaSom(valor) {
      this.preferencias = { ...this.preferencias, som: valor };
      SalvarPreferencias(this.preferencias);
      if (valor) prepararSons();
    },

    definirPreferenciaVolume(valor) {
      const v = Math.min(1, Math.max(0, Number(valor)));
      this.preferencias = { ...this.preferencias, volume: v };
      SalvarPreferencias(this.preferencias);
    },

    definirPreferenciaDaltonismo(valor) {
      this.preferencias = { ...this.preferencias, daltonismo: valor };
      SalvarPreferencias(this.preferencias);
      AplicarDaltonismo(valor);
    },

    linkDesafio(codigo) {
      const c = (codigo || this.codigoDesafio || this.codigoSala || "")
        .trim()
        .toUpperCase();
      return c ? `${location.origin}/?sala=${c}` : location.origin;
    },

    async copiarTexto(texto, msgOk = "Copiado!") {
      try {
        await navigator.clipboard.writeText(texto);
        this.mostrarToast(msgOk, false, true);
      } catch {
        this.mostrarToast("Não foi possível copiar", true);
      }
    },

    async compartilharResultado() {
      const texto = this.resultado.gradeTexto;
      if (navigator.share) {
        try {
          await navigator.share({ title: "Termo", text: texto });
          return;
        } catch {
          /* fallback */
        }
      }
      await this.copiarTexto(texto, "Resultado copiado!");
    },

    jogarDeNovo() {
      this.fecharDialogs();
      if (this.modo === "pratica") this.iniciarModo("pratica");
      else if (EhModoSalaOnline(this.modo) && this.codigoSala) {
        this.encerrada = false;
        if (this.modo === "arena") {
          this.irParaView("arenaLobby");
        }
        this.conectarWs();
      } else this.voltarInicio();
    },

    async criarDesafio() {
      this.nick = this.nickJogo;
      SalvarNickLocal(this.nick);
      try {
        const D = await api.desafioCriar();
        const cod = D.codigoSala || D.codigoDesafio;
        this.codigoDesafio = cod;
        this.entrarNaSala(D);
        await this.copiarTexto(
          `${location.origin}/?sala=${cod}`,
          `Sala ${cod} — link copiado!`
        );
      } catch (e) {
        this.mostrarToast(e.message || "Erro ao criar desafio", true);
      }
    },

    registrarPersistenciaAoRecarregar() {
      if (listenerPersistirPagina) return;
      listenerPersistirPagina = () => {
        if (
          EhModoSalaOnline(this.modo) &&
          this.codigoSala &&
          this.idJogador &&
          !this.dadosSala?.partidaEncerrada
        ) {
          this.persistir();
        }
      };
      window.addEventListener("pagehide", listenerPersistirPagina);

      if (listenerSessaoOutraAba) return;
      listenerSessaoOutraAba = (e) => {
        if (e.key !== CHAVE_SESSAO || e.newValue == null) return;
        if (DeveIgnorarSincronizacaoOutraAba(this)) return;
        this.mostrarToast(
          "Outra aba atualizou sua sessão — sincronizando…",
          false
        );
        this.retomarSessao().catch(() => {});
      };
      window.addEventListener("storage", listenerSessaoOutraAba);
      RegistrarListenerSessaoOutrasAbas(() => {
        if (DeveIgnorarSincronizacaoOutraAba(this)) return;
        this.mostrarToast("Outra aba atualizou a partida — sincronizando…", false);
        this.retomarSessao().catch(() => {});
      });
    },

    registrarSincronizarAoVoltar() {
      if (listenerVisibilidadeApp) return;
      const store = this;
      listenerVisibilidadeApp = () => {
        if (document.visibilityState !== "visible") return;
        if (store.view === "inicio") {
          store.carregarJogoAtivo();
          store.carregarSalasPublicas();
          if (!store.lobbyWsConectado) store.conectarLobbyWs();
          return;
        }
        if (EhModoSalaOnline(store.modo) && store.codigoSala && store.idJogador) {
          acoesArena.sincronizarArenaHttp(store);
          if (!store.wsConectado && store.view !== "inicio") {
            store.conectarWs();
          }
          if (store.jogoAtivo?.ativo) {
            store.carregarJogoAtivo();
          }
        }
      };
      document.addEventListener("visibilitychange", listenerVisibilidadeApp);
    },

    async inicializar() {
      this.registrarPersistenciaAoRecarregar();
      this.registrarSincronizarAoVoltar();
      LimparCodigoSala();
      this.codigoEntrada = "";
      this.aplicarQueryDesafio();
      AplicarDaltonismo(this.preferencias.daltonismo);
      document.documentElement.classList.toggle(
        "reduzir-animacao",
        !!this.preferencias.reduzirAnimacao
      );
      AplicarTema(this.preferencias);
      if (pararObservadorTema) pararObservadorTema();
      pararObservadorTema = ObservarTemaSistema(() => {
        if ((this.preferencias.temaModo || "sistema") === "sistema") {
          AplicarTema(this.preferencias);
        }
      });
      cacheDicionarioSet = await GarantirCacheDicionario();
      await SincronizarTempoServidor();
      if (this.token) {
        await this.sincronizarContaServidor();
      }
      await this.carregarFrasesChat();
      this.fecharDialogs();
      this.atualizarStatsUI();
      const salvo = ObterSessao();
      await this.carregarJogoAtivo();

      let retomou = false;
      if (await this.sincronizarFilaRanqueadaInicial()) {
        retomou = true;
      }

      const J = this.jogoAtivo;
      if (!retomou && J?.ativo && (J.somenteResultado || J.resultadoPendente)) {
        await this.reconectarJogoAtivo();
        retomou = true;
      } else if (!retomou) {
        const estavaNoJogo =
          salvo?.ranqueada?.view === "jogo" || salvo?.arena?.view === "jogo";
        const partidaVivaNoHero =
          J?.ativo &&
          EhJogoAtivoOnline(J) &&
          !J.somenteResultado &&
          !J.resultadoPendente &&
          !J.partidaEncerrada;
        if (estavaNoJogo || partidaVivaNoHero) {
          retomou = await this.retomarSessao();
          if (!retomou && partidaVivaNoHero) {
            await this.reconectarJogoAtivo();
            retomou =
              this.view === "jogo" ||
              PartidaRanqueadaAtiva(this) ||
              (this.modo === "arena" && !!this.codigoSala);
          }
        }
      }

      await Promise.all([this.carregarInfoDiaria(), this.carregarHomePainel()]);
      const temConviteSala = !!this.capturarConviteSalaDaUrl();
      this.mostrarTutorial = false;
      if (!retomou) {
        this.irParaView("inicio");
        if (temConviteSala) {
          await this.processarConviteAposBoot(false);
        } else if (!localStorage.getItem(CHAVE_TUTORIAL_VISTO)) {
          this.mostrarTutorial = true;
        } else if (!this.token && !this.conta) {
          setTimeout(() => this.abrirConta("entrada"), 500);
        }
      } else if (temConviteSala) {
        await this.processarConviteAposBoot(true);
      }
      const desafio = new URLSearchParams(location.search).get("desafio");
      if (desafio && !temConviteSala) {
        const cod = desafio.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
        if (cod.length === 6) {
          this.conviteSalaCodigo = cod;
          await this.processarConviteAposBoot(retomou);
        } else if (!retomou) {
          this.codigoDesafio = cod;
          this.abrirDialog("jogar");
        }
      }
    },
  },
});
