/** Partidas solo: persistência, multi-tabuleiro e chutes via API. */
import { api } from "../../services/api.js";
import { TocarSom } from "../../lib/som.js";
import { AgendarFimAnimacao, DURACAO_FLIP_LINHA } from "../../utils/animacao.js";
import { CHAVE_TUTORIAL_MULTI } from "../../utils/constantes.js";
import { EhModoSalaOnline } from "../../utils/modos.js";
import {
  NormalizarTentativa,
  RegistrarLetrasNoTeclado,
  LetrasEmProgressoSalvas,
  LetrasVazias,
  LetrasPreenchidas,
  MontarPalavraChute,
  PalavraJaFoiTentada,
  ProximoIndiceVazio,
  ValidarModoDificilClient,
} from "../../utils/jogo.js";
import {
  PersistirSessao,
  LimparSessao,
  SalvarNickLocal,
} from "../../utils/sessao.js";
import { PalavraNoCache } from "../../utils/dicionario-cache.js";
import { MontarResultadoUi } from "../../utils/jogo.js";
import { ObterStats, DiariaJaJogadaLocal } from "../../utils/stats.js";

export function persistir() {
  PersistirSessao(this.$state);
}

export function criarGradesMulti(qtd) {
  this.gradesMulti = Array.from({ length: qtd }, () => ({
    tentativas: [],
  }));
}

export function aplicarChuteMulti(linhas, indiceTentativa, animar = false) {
  if (!linhas) return;
  linhas.forEach((linha) => {
    const g = this.gradesMulti[linha.indice];
    if (!g) return;
    if (linha.venceu && !linha.estados?.length) {
      const tab = this.tabuleiros?.[linha.indice];
      const ult = tab?.tentativas?.[tab.tentativas.length - 1];
      if (ult) {
        const t = { ...NormalizarTentativa(ult), animar: !!animar };
        g.tentativas[indiceTentativa] = t;
        if (animar) AgendarFimAnimacao(t);
      }
      return;
    }
    const t = { ...NormalizarTentativa(linha), animar: !!animar };
    g.tentativas[indiceTentativa] = t;
    if (animar) AgendarFimAnimacao(t);
    if (linha.estados?.length) {
      this.teclado = RegistrarLetrasNoTeclado(linha, this.teclado);
    }
  });
}

export function restaurarPartidaSolo(D, salvoSolo) {
  this.maxTentativas = D.maximoTentativas || 6;
  this.encerrada = !!D.encerrada;
  this.tabuleiros = D.tabuleiros || null;
  const tentativas = (D.tentativas || []).map(NormalizarTentativa);

  if (D.tabuleiros?.length > 1) {
    criarGradesMulti.call(this, D.tabuleiros.length);
    this.tentativasHist = [...tentativas];
    this.teclado = { ...(salvoSolo?.teclado || {}) };
    tentativas.forEach((tent, idx) => {
      if (!tent.linhas) return;
      aplicarChuteMulti.call(this, tent.linhas, idx);
      tent.linhas.forEach((linha) => {
        if (linha.estados?.length) {
          this.teclado = RegistrarLetrasNoTeclado(linha, this.teclado);
        }
      });
    });
  } else {
    this.teclado = { ...(salvoSolo?.teclado || {}) };
    tentativas.forEach((t) => {
      this.teclado = RegistrarLetrasNoTeclado(t, this.teclado);
    });
    this.tentativasHist = tentativas;
  }

  this.tentativa = tentativas.length;
  if (this.encerrada) {
    this.letras = LetrasVazias();
    this.indiceCursor = 0;
  } else {
    this.letras = LetrasEmProgressoSalvas(salvoSolo);
    this.indiceCursor =
      typeof salvoSolo?.indiceCursor === "number"
        ? salvoSolo.indiceCursor
        : ProximoIndiceVazio(this.letras);
  }
}

export function revelarTentativaSolo(indice, tentativa, animar = false) {
  const t = { ...NormalizarTentativa(tentativa), animar: !!animar };
  this.tentativasHist[indice] = t;
  if (animar) AgendarFimAnimacao(t);
}

export async function enviarChuteSolo(cacheDicionarioSet) {
  if (!LetrasPreenchidas(this.letras)) {
    this.mostrarToast("Preencha as 5 letras", true);
    return;
  }
  const palavra = MontarPalavraChute(this.letras);
  const tentativasAnteriores = this.tentativasHist;
  if (PalavraJaFoiTentada(palavra, tentativasAnteriores)) {
    this.tratarChuteInvalido("Você já tentou essa palavra.");
    return;
  }
  const noCache = PalavraNoCache(palavra, cacheDicionarioSet);
  if (noCache === false) {
    this.tratarChuteInvalido("Palavra não encontrada no dicionário.");
    return;
  }
  if (noCache === null && !cacheDicionarioSet) {
    this.mostrarToast("Validando no servidor…", false);
  }
  if (this.dificuldade === "dificil") {
    const { ok, msg } = ValidarModoDificilClient(palavra, tentativasAnteriores);
    if (!ok) {
      this.tratarChuteInvalido(msg);
      return;
    }
  }

  this.carregandoChute = true;
  try {
    const D = await api.jogarChute({
      idPartida: this.idPartida,
      tokenPartida: this.tokenPartida,
      palavra,
      nomeJogador: this.nickJogo,
    });

    if (!D.valido) {
      this.tratarChuteInvalido(D.mensagem);
      return;
    }

    this.mostrarToast("");
    const idx = this.tentativa;
    if (D.tentativa.linhas) {
      aplicarChuteMulti.call(this, D.tentativa.linhas, idx, true);
      this.tabuleiros = D.tabuleiros;
      this.tentativasHist.push({ ...D.tentativa });
    } else {
      revelarTentativaSolo.call(this, idx, D.tentativa, true);
      this.teclado = RegistrarLetrasNoTeclado(D.tentativa, this.teclado);
    }
    this.tentativa++;
    this.letras = LetrasVazias();
    this.indiceCursor = 0;

    if (D.venceu || D.tentativa.linhas?.some((L) => L.venceu)) {
      TocarSom("acerto");
    } else {
      TocarSom("chute");
    }

    if (D.progresso) {
      this.aplicarProgressoResposta(D.progresso);
    }

    if (D.encerrada) {
      this.encerrada = true;
      LimparSessao();
      this.registrarVitoria(D.modo, D.tentativasUsadas, D.venceu);
      const palavraFim =
        D.palavrasSecretas?.join(", ") || D.palavraSecreta || "";
      setTimeout(() => {
        if (D.venceu) TocarSom("vitoria");
        this.mostrarResultadoSolo(
          D.venceu,
          palavraFim,
          D.pontos,
          D.modo,
          D.tentativasUsadas
        );
      }, DURACAO_FLIP_LINHA + 80);
    } else {
      persistir.call(this);
    }
  } finally {
    this.carregandoChute = false;
  }
}

export async function iniciarModo(modo, opcoes = {}) {
  this.nick = this.nickJogo;
  SalvarNickLocal(this.nick);
  const dificuldade = opcoes.dificuldade || this.dificuldade;
  const codigoDesafio = opcoes.codigoDesafio || null;

  if (modo === "diaria") {
    if (!this.conta?.podeRanqueada) {
      if (this.conta?.ehVisitante) this.abrirCriarConta();
      else this.abrirLoginConta();
      return;
    }
    try {
      const info = await api.diariaInfo(this.nickJogo);
      if (info.jaJogou) {
        const S = ObterStats();
        const grade = S.ultimaGrade || info.resultado?.gradeTexto || "";
        if (grade) {
          this.resultado = MontarResultadoUi({
            modo: "diaria",
            venceu: !!info.resultado?.venceu,
            tentativa: info.resultado?.tentativasUsadas || 0,
            maxTentativas: info.maximoTentativas || 6,
            gradeTexto: grade,
            pontos: info.resultado?.pontos,
            dataDia: info.dataDia,
          });
          this.resultado.titulo = "Seu resultado de hoje";
          this.abrirDialog("resultado");
        } else {
          this.mostrarToast("Você já jogou a palavra do dia hoje.", true);
        }
        return;
      }
    } catch (e) {
      this.mostrarToast(
        e.message || "Não foi possível verificar a palavra do dia.",
        true
      );
      return;
    }
  }

  LimparSessao();
  this.modo = modo;
  try {
    const D = await api.jogarIniciar({
      nomeJogador: this.nickJogo,
      modo,
      dificuldade,
      codigoDesafio,
    });
    this.idPartida = D.idPartida;
    this.tokenPartida = D.tokenPartida || null;
    this.dataDia = D.dataDia;
    this.maxTentativas = D.maximoTentativas || 6;
    this.tabuleiros = D.tabuleiros || null;
    const labels = {
      diaria: "Palavra do dia",
      pratica: "Prática",
      dueto: "Dueto",
      quarteto: "Quarteto",
      desafio: `Desafio ${codigoDesafio || ""}`.trim(),
    };
    this.iniciarTelaJogo(labels[modo] || modo);
    if (D.tabuleiros?.length > 1) {
      criarGradesMulti.call(this, D.tabuleiros.length);
      if (!localStorage.getItem(CHAVE_TUTORIAL_MULTI)) {
        localStorage.setItem(CHAVE_TUTORIAL_MULTI, "1");
        this.mostrarAviso({
          titulo: "Dueto e Quarteto",
          mensagem:
            "Um chute vale para todas as palavras ao mesmo tempo. Cada grade tem sua própria resposta — as cores podem ser diferentes entre elas.",
          dica: "Você tem mais tentativas que no modo clássico.",
        });
      }
    }
    persistir.call(this);
    this.fecharDialogs();
  } catch (e) {
    this.mostrarToast(e.message || "Não foi possível iniciar", true);
  }
}

export const acoesSolo = {
  persistir,
  criarGradesMulti,
  aplicarChuteMulti,
  restaurarPartidaSolo,
  revelarTentativaSolo,
  enviarChuteSolo,
  iniciarModo,
};
