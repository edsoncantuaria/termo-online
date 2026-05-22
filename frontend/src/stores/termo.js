import { defineStore } from "pinia";
import { api } from "../services/api.js";
import {
  TAMANHO_PALAVRA,
  TECLADO_LINHAS,
  CHAT_VIDA_MS,
  CHAT_MAX_VISIVEIS,
  DURACAO_TOAST_MS,
  CHAVE_TUTORIAL_VISTO,
  CHAVE_TUTORIAL_MULTI,
} from "../utils/constantes.js";
import { TextoProximaDiaria } from "../utils/diaria.js";
import {
  CarregarAuthLocal,
  SalvarAuthLocal,
  LimparAuthLocal,
} from "../utils/auth.js";
import { EhModoSalaOnline } from "../utils/modos.js";
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
import { TextoXpGanho } from "../utils/progresso.js";
import { acoesRanqueada } from "./termo/acoes-ranqueada.js";
import { acoesSolo } from "./termo/acoes-solo.js";
import { acoesResultado } from "./termo/acoes-resultado.js";
import {
  ObterSessao,
  LimparSessao,
  PersistirSessao,
  SalvarCodigoSala,
  CarregarCodigoSala,
  CarregarNickLocal,
  SalvarNickLocal,
} from "../utils/sessao.js";
import {
  ObterStats,
  SalvarStats,
  DiariaJaJogadaLocal,
} from "../utils/stats.js";
import {
  ObterPreferencias,
  SalvarPreferencias,
  AplicarDaltonismo,
  AplicarTema,
  ObservarTemaSistema,
} from "../lib/extras.js";
import {
  GarantirCacheDicionario,
  PalavraNoCache,
} from "../utils/dicionario-cache.js";
import { DataHojeIsoBrasil } from "../utils/tempo-brasil.js";
import * as acoesArena from "./termo/acoes-arena.js";
import { TocarSom, prepararSons } from "../lib/som.js";
import { AgendarFimAnimacao, DURACAO_FLIP_LINHA } from "../utils/animacao.js";

let socketLobby = null;
let tentativasReconexaoLobby = 0;
let intervaloTimer = null;
let timersChat = new Map();
let cacheDicionarioSet = null;
let pararObservadorTema = null;
let timerToast = null;

function ChaveMsgChat(M) {
  return `${M.quando}|${M.idJogador}|${M.texto}`;
}

export const useTermoStore = defineStore("termo", {
  state: () => ({
    view: "inicio",
    nick: CarregarNickLocal(),
    codigoEntrada: CarregarCodigoSala(),
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
    filaJogadoresOnline: 0,
    filaPreview: [],
    filaBusca: null,
    minhaPosicaoRanqueada: null,
    totalRanqueados: 0,
    rankingRanqueado: [],
    bannerReconexao: false,
    wsConectado: false,
    lobbyWsConectado: false,
    lobbyWsReconectando: false,

    modo: null,
    idPartida: null,
    tokenPartida: null,
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

    preferencias: ObterPreferencias(),
    frasesChat: [],

    chatMensagens: [],
    cronometroTexto: "",
    cronometroUrgente: false,
    cronometroVisivel: false,
    countdownSegundos: null,
    toastVitoriaRodada: "",

    dialogAberto: null,
    dialogContaModo: "entrada",
    dialogContaForcarRegistro: false,
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
      mesmaPalavra: true,
      verOutros: true,
      modoSessao: "pontos",
      metaVitorias: 5,
      inicioAutoDois: false,
      tempoLimite: 180,
      senha: "",
    },

    tentativasReconexao: 0,
    wsUrl: null,
  }),

  getters: {
    nickJogo: (s) => {
      const N = (s.conta?.nick || s.nick || "Jogador").trim().slice(0, 24);
      return N || "Jogador";
    },
    tecladoLinhas: () => [
      TECLADO_LINHAS[0],
      TECLADO_LINHAS[1],
      ["enter", ...TECLADO_LINHAS[2], "back"],
    ],
    emJogo: (s) => s.view === "jogo",
    emLobby: (s) => s.view === "arenaLobby",
    modoJogoArena: (s) => s.view === "jogo" && EhModoSalaOnline(s.modo),
    modoJogoRanqueada: (s) => s.view === "jogo" && s.modo === "ranqueada",
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
          s.modo === "ranqueada" ? " · duelo ranqueado" : "";
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
      return j.filter((x) => !x.souEu);
    },
    tituloOutros: (s) => {
      const n = s.outrosNaRodada.length;
      if (!n) return "Na rodada";
      return n === 1
        ? "Na rodada · 1 jogador"
        : `Na rodada · ${n} jogadores`;
    },
    lateralVisivel: (s) =>
      s.modoJogoArena &&
      (s.outrosNaRodada.length > 0 || s.emJogo),
    painelChatVisivel: (s) => s.modoJogoArena,
    painelEntreRodadas: (s) =>
      s.dadosSala?.estadoSala === "entre_rodadas" &&
      !s.dadosSala?.partidaEncerrada,
    badgeEstadoJogo: (s) => {
      const D = s.dadosSala;
      if (!D || !EhModoSalaOnline(s.modo)) return null;
      if (D.estadoSala === "entre_rodadas") {
        return { tipo: "pausa", texto: "Rodada encerrada" };
      }
      if (D.estadoSala === "countdown") {
        return { tipo: "prep", texto: "Próxima rodada em instantes…" };
      }
      if (D.estadoSala === "jogando") {
        const eu = D.jogadores?.find((j) => j.souEu);
        if (eu?.venceu) return { tipo: "ok", texto: "Você acertou a palavra!" };
        if (eu?.finalizou) return { tipo: "aguardo", texto: "Aguardando outros jogadores" };
        return { tipo: "ativo", texto: "Rodada em andamento" };
      }
      return null;
    },
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
      return lista.map((j, i) => ({
        ...j,
        posicao: i + 1,
        progresso: porVitorias
          ? Math.min(100, ((j.vitoriasRodada || 0) / meta) * 100)
          : Math.min(100, ((j.pontosAcumulados || 0) / maxPts) * 100),
      }));
    },
    mostrarDicaCelulas: (s) => {
      if (s.encerrada || s.espectador || !s.mostrarGradePrincipal) return false;
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
          !s.encerrada &&
          !EhModoSalaOnline(s.modo)
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
        } else if (
          i === s.tentativa &&
          !s.encerrada &&
          EhModoSalaOnline(s.modo)
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
        atual: i === s.tentativa && !s.encerrada,
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
      this.letras = LetrasVazias();
      this.indiceCursor = 0;
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
      if (this.view === "inicio") return Promise.resolve();
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
        this.view === "jogo" &&
        EhModoSalaOnline(this.modo) &&
        !this.espectador
      ) {
        titulo =
          this.modo === "ranqueada"
            ? "Sair do duelo ranqueado?"
            : "Sair da partida?";
        mensagem =
          this.modo === "ranqueada"
            ? "Você abandonará o duelo e sairá da fila."
            : "Você será removido da sala.";
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
      if (!this.conta) {
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

    aplicarSessaoConta(conta, token) {
      this.conta = conta;
      this.token = token;
      SalvarAuthLocal(token, conta);
      if (conta?.nick) {
        this.nick = conta.nick;
        SalvarNickLocal(conta.nick);
      }
    },

    async authLogin(identificador, senha) {
      try {
        const D = await api.authLogin(identificador, senha);
        this.aplicarSessaoConta(D.conta, D.token);
        this.fecharDialogs();
        this.mostrarToast(
          `Bem-vindo, ${NickExibicao(D.conta.nick)}!`,
          false,
          true
        );
      } catch (e) {
        this.mostrarToast(e.message, true);
      }
    },

    async authRegistrar(nick, email, senha) {
      try {
        const D = await api.authRegistrar(nick, email, senha);
        this.aplicarSessaoConta(D.conta, D.token);
        this.fecharDialogs();
        this.mostrarToast("Conta criada com sucesso!", false, true);
      } catch (e) {
        this.mostrarToast(e.message, true);
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
      const Base = this.normalizarNickEntrada(nickEscolhido);
      if (Base.length < 3) {
        this.mostrarToast(
          "Escolha um nome com pelo menos 3 letras (a–z, números ou _).",
          true
        );
        return;
      }
      try {
        const D = await api.authVisitante(Base);
        this.aplicarSessaoConta(D.conta, D.token);
        this.fecharDialogs();
        const exib = NickExibicao(D.conta.nick);
        const sufixo =
          D.conta.nick !== Base
            ? ` (${exib} — nome já em uso, variante atribuída)`
            : "";
        this.mostrarToast(
          `Você entrou como ${exib}${sufixo}`,
          false,
          true
        );
      } catch (e) {
        this.mostrarToast(e.message, true);
      }
    },

    exigirContaRegistrada() {
      if (this.conta?.podeRanqueada) return true;
      if (this.conta?.ehVisitante) this.abrirCriarConta();
      else this.abrirConta("registro");
      return false;
    },

    authSair() {
      this.pararFilaRanqueada();
      LimparAuthLocal();
      this.conta = null;
      this.token = null;
      this.fecharDialogs();
    },

    abrirConta(modo = "entrada") {
      this.dialogContaModo = modo;
      this.dialogContaForcarRegistro = modo === "registro";
      this.abrirDialog("conta");
    },

    abrirCriarConta() {
      this.dialogContaModo = "registro";
      this.dialogContaForcarRegistro = true;
      this.dialogContaNickSugerido = this.conta?.nick || "";
      this.abrirDialog("conta");
    },

    ...acoesRanqueada,
    ...acoesSolo,
    ...acoesResultado,

    irParaView(nome) {
      this.view = nome;
      if (nome === "inicio") {
        this.fecharDialogs();
        this.conectarLobbyWs();
      } else {
        this.pararLobbyWs();
      }
      if (nome !== "jogo") {
        this.countdownSegundos = null;
        this.pararCronometro();
      }
    },

    pararLobbyWs() {
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
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      const url = `${proto}//${location.host}/ws/lobby`;
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
          this.carregarSalasPublicas();
        }
      };
    },

    fecharDialogs() {
      if (this.dialogAberto === "jogar" && this.filaRanqueada) {
        this.pararFilaRanqueada();
      }
      this.dialogAberto = null;
      this.aviso.aoConfirmar = null;
      this.aviso.aoCancelar = null;
      this.dialogContaForcarRegistro = false;
      this.dialogContaNickSugerido = "";
    },

    abrirDialog(nome) {
      const anterior = this.dialogAberto;
      if (anterior === "jogar" && this.filaRanqueada && nome !== "jogar") {
        this.pararFilaRanqueada();
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

    definirNick(valor) {
      this.nick = (valor || "Jogador").trim().slice(0, 24) || "Jogador";
      SalvarNickLocal(this.nick);
      this.carregarInfoDiaria();
    },

    resetarJogo() {
      this.pararCronometro();
      this.tentativa = 0;
      this.letras = LetrasVazias();
      this.indiceCursor = 0;
      this.encerrada = false;
      this.teclado = {};
      this.tentativasHist = [];
      this.tabuleiros = null;
      this.gradesMulti = [];
      this.arenaTentativas = [];
      this.arenaTentativasExibidas = 0;
      this.arenaRodadaSync = null;
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
        if (D.jaJogou || DiariaJaJogadaLocal()) {
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
      const S = ObterStats();
      S.vitorias = (S.vitorias || 0) + (venceu ? 1 : 0);
      S.sequencia = venceu ? (S.sequencia || 0) + 1 : 0;
      if (modo === "diaria") {
        S.ultimaDiaria = this.dataDia || DataHojeIsoBrasil();
        S.diariaVenceu = venceu;
        S.ultimaTentativas = tentativas;
      }
      SalvarStats(S);
      this.statsLocais = S;
    },

    selecionarCelula(indice) {
      if (this.encerrada) return;
      if (indice < 0 || indice >= TAMANHO_PALAVRA) return;
      this.indiceCursor = indice;
      if (this.modo && !EhModoSalaOnline(this.modo) && this.idPartida) {
        this.persistir();
      }
    },

    onTecla(k) {
      if (this.encerrada) return;
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
          sock.send(
            JSON.stringify({
              tipo: "chute",
              dados: { palavra },
            })
          );
          this.letras = LetrasVazias();
          this.indiceCursor = 0;
        }
        return;
      }

      return acoesSolo.enviarChuteSolo.call(this, cacheDicionarioSet);
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
        aoConfirmar: aoConfirmar || null,
        aoCancelar: aoCancelar || null,
      };
      this.abrirDialog("aviso");
    },

    cancelarAviso() {
      const cb = this.aviso.aoCancelar;
      this.fecharDialogs();
      cb?.();
    },

    confirmarAviso() {
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
      ev?.preventDefault?.();
      this.nick = this.nickJogo;
      SalvarNickLocal(this.nick);
      const c = this.formCriarSala;
      try {
        const D = await api.salaCriar({
          nomeJogador: this.nickJogo,
          salaPublica: !c.senha?.trim(),
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
      this.souCriador = D.souCriador;
      this.codigoEntrada = D.codigoSala;
      SalvarCodigoSala(D.codigoSala);
      this.dadosSala = D;
      this.fecharDialogs();
      if (D.estadoSala === "aguardando") {
        this.irParaView("arenaLobby");
      }
      this.conectarWs();
      this.persistir();
    },

    async entrarSala() {
      this.nick = this.nickJogo;
      SalvarNickLocal(this.nick);
      const cod = this.codigoEntrada.trim().toUpperCase();
      if (cod.length !== 6) {
        this.mostrarAviso({
          titulo: "Código inválido",
          mensagem: "Digite as 6 letras do código da sala para entrar.",
          dica: "O código aparece na tela de quem criou a sala.",
        });
        return;
      }
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
      } catch (e) {
        const msg = e.message || "Não foi possível entrar";
        const conflito = EhErroNick(msg);
        this.mostrarAviso({
          titulo: conflito ? "Nick já em uso" : "Não foi possível entrar",
          mensagem: conflito
            ? `Alguém na sala já está como «${this.nickJogo}». Troque seu apelido e tente de novo.`
            : msg,
          dica: conflito
            ? "Use um nick diferente do que já está na lista de jogadores."
            : undefined,
          tipo: conflito ? "nick" : "erro",
          aoConfirmar: conflito ? () => this.entrarSala() : undefined,
        });
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

    atualizarArena(D) {
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
      this.estadoSalaArena = D.estadoSala;
      this.dadosSala = D;
      this.espectador = !!eu?.espectador;
      this.souCriador = D.souCriador ?? this.souCriador;

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
        this.view !== "jogo" &&
        !this.espectador
      ) {
        this.iniciarTelaJogo(labelJogo);
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
        this.arenaTentativas = [];
        this.arenaTentativasExibidas = 0;
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
        this.ultimoToastRodadaFim = null;
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
        eu.tentativas?.forEach((t) => {
          this.teclado = RegistrarLetrasNoTeclado(t, this.teclado);
        });
        this.tentativa = total;
        this.arenaTentativasExibidas = total;
        this.encerrada = !!eu.finalizou;
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
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
      } else if (this.view === "jogo" && D.estadoSala === "countdown") {
        this.encerrada = true;
        this.letras = LetrasVazias();
        this.indiceCursor = 0;
      }

      this.renderizarChat(D);
      this.atualizarEntreRodadas(D);

      if (
        this.view === "jogo" &&
        D.estadoSala === "countdown" &&
        D.countdownSegundos != null
      ) {
        this.countdownSegundos = Math.max(1, D.countdownSegundos);
      } else if (this.view !== "jogo") {
        this.countdownSegundos = null;
      }

      this.ultimoVencedorRodadaId = D.ultimoVencedorRodadaId;
      if (
        D.estadoSala === "entre_rodadas" &&
        D.rodadaAtual != null &&
        D.rodadaAtual !== this.ultimoToastRodadaFim
      ) {
        this.ultimoToastRodadaFim = D.rodadaAtual;
        const verdes = D.maxVerdesRodada ?? 0;
        if (D.rodadaPorVerdes) {
          const ids = D.vencedoresRodadaIds || [];
          const eu = ids.includes(this.idJogador);
          if (D.empateVerdesRodada && ids.length > 1) {
            this.toastVitoriaRodada = eu
              ? `Empate! +1 pt (${verdes} verdes)`
              : `Empate na rodada (${verdes} verdes)`;
            if (eu) TocarSom("vitoria");
          } else if (ids.length === 1) {
            const nome =
              D.vencedoresRodadaNomes?.[0] || D.ultimoVencedorRodada || "?";
            this.toastVitoriaRodada = eu
              ? `+1 pt (${verdes} verdes)!`
              : `${nome} venceu (${verdes} verdes)`;
            if (eu) TocarSom("vitoria");
          }
        } else if (D.ultimoVencedorRodada) {
          const euVenceu = D.ultimoVencedorRodadaId === this.idJogador;
          this.toastVitoriaRodada = euVenceu
            ? "+1 vitória de rodada!"
            : `${D.ultimoVencedorRodada} venceu a rodada`;
          if (euVenceu) TocarSom("vitoria");
        }
        if (this.toastVitoriaRodada) {
          setTimeout(() => {
            this.toastVitoriaRodada = "";
          }, 2800);
        }
      }

      if (D.progressoEvento) {
        this.aplicarProgressoResposta(D.progressoEvento);
      }

      this.persistir();

      if (D.partidaEncerrada) {
        this.pararCronometro();
        this.encerrada = true;
        const campeao = D.placar?.[0];
        const venci = D.vencedorId === this.idJogador;
        setTimeout(() => this.mostrarResultadoArena(D, venci, campeao), 300);
        acoesArena.fecharSocketSala();
        this.irParaView("inicio");
        if (this.modo === "ranqueada") {
          this.modo = null;
          this.codigoSala = null;
          this.idJogador = null;
          this.dadosSala = null;
          LimparSessao();
        }
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
      this.chatMensagens = [];
    },

    renderizarChat(D) {
      const msgs = D.mensagensChat || [];
      for (const M of msgs) {
        const chave = ChaveMsgChat(M);
        if (this.chatMensagens.some((x) => x.chave === chave)) continue;
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

    async voltarInicio() {
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
      const salvo = ObterSessao();
      if (!salvo) return false;
      let retomou = false;

      const retomarSala = async (chave, modo, viewLobby, label) => {
        const S = salvo[chave];
        if (!S) return false;
        try {
          const R = await api.salaEstado(S.codigoSala, S.idJogador);
          if (!R.ok) throw new Error("sala");
          const D = await R.json();
          if (D.partidaEncerrada) throw new Error("fim");
          this.modo = modo;
          this.codigoSala = S.codigoSala;
          this.idJogador = S.idJogador;
          this.souCriador = D.souCriador;
          this.configArena = D.configuracao;
          this.codigoEntrada = S.codigoSala;
          SalvarCodigoSala(S.codigoSala);
          this.dadosSala = D;
          if (D.estadoSala === "aguardando") {
            this.irParaView(viewLobby);
          }
          this.conectarWs();
          if (
            D.estadoSala === "jogando" ||
            D.estadoSala === "entre_rodadas" ||
            D.estadoSala === "countdown"
          ) {
            this.iniciarTelaJogo(label);
            this.atualizarArena(D);
          }
          this.persistir();
          this.mostrarToast(
            modo === "ranqueada"
              ? "Ranqueado retomado — duelo em andamento"
              : "Arena retomada — você voltou à sala"
          );
          return true;
        } catch {
          return false;
        }
      };

      if (salvo.ranqueada) {
        retomou = await retomarSala(
          "ranqueada",
          "ranqueada",
          "inicio",
          "Ranqueado"
        );
        if (!retomou) {
          const s = ObterSessao();
          if (s?.solo) {
            localStorage.setItem(
              "termoSessao",
              JSON.stringify({ solo: s.solo })
            );
          } else LimparSessao();
        }
      }

      if (!retomou && salvo.arena) {
        retomou = await retomarSala(
          "arena",
          "arena",
          "arenaLobby",
          "Arena"
        );
        if (!retomou) {
          const s = ObterSessao();
          if (s?.solo) {
            localStorage.setItem(
              "termoSessao",
              JSON.stringify({ solo: s.solo })
            );
          } else LimparSessao();
        }
      }

      if (salvo.solo && !retomou) {
        if (salvo.solo.modo === "diaria" && DiariaJaJogadaLocal()) {
          LimparSessao();
          return false;
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
      } catch {
        this.salasPublicas = [];
      }
    },

    async carregarHomePainel() {
      this.carregandoHome = true;
      try {
        await this.carregarSalasPublicas();
      } finally {
        this.carregandoHome = false;
      }
    },

    async abrirPerfil() {
      if (!this.exigirContaRegistrada()) return;
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

    aplicarQuerySala() {
      const cod = new URLSearchParams(location.search).get("sala");
      if (cod) this.codigoEntrada = cod.toUpperCase();
    },

    aplicarQueryDesafio() {
      const d = new URLSearchParams(location.search).get("desafio");
      if (d) this.codigoDesafio = d.toUpperCase();
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
      const c = (codigo || this.codigoDesafio || "").trim().toUpperCase();
      return c ? `${location.origin}/?desafio=${c}` : location.origin;
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
        this.conectarWs();
      } else this.voltarInicio();
    },

    async criarDesafio() {
      try {
        const D = await api.desafioCriar();
        this.codigoDesafio = D.codigoDesafio;
        await this.copiarTexto(
          `${location.origin}/?desafio=${D.codigoDesafio}`,
          `Desafio ${D.codigoDesafio} — link copiado!`
        );
      } catch {
        this.mostrarToast("Erro ao criar desafio", true);
      }
    },

    async inicializar() {
      this.aplicarQuerySala();
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
      if (this.token) {
        try {
          const D = await api.authEu();
          this.aplicarSessaoConta(D.conta, this.token);
        } catch {
          this.authSair();
        }
      }
      await this.carregarFrasesChat();
      this.fecharDialogs();
      this.atualizarStatsUI();
      const retomou = await this.retomarSessao();
      await Promise.all([this.carregarInfoDiaria(), this.carregarHomePainel()]);
      if (!retomou) {
        this.irParaView("inicio");
        if (!localStorage.getItem(CHAVE_TUTORIAL_VISTO)) {
          this.mostrarTutorial = true;
        } else if (!this.conta) {
          setTimeout(() => this.abrirConta("entrada"), 500);
        }
      }
      const desafio = new URLSearchParams(location.search).get("desafio");
      if (desafio && !retomou) {
        this.codigoDesafio = desafio.toUpperCase();
        this.abrirDialog("jogar");
      }
    },
  },
});
