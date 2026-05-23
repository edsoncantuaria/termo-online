/** Prática 100% local (online ou offline) — sem API, XP nem estatísticas. */
import { TocarSom } from "../../lib/som.js";
import { AgendarFimAnimacao, DURACAO_FLIP_LINHA } from "../../utils/animacao.js";
import { GarantirCacheDicionario } from "../../utils/dicionario-cache.js";
import {
  EscolherPalavraAleatoria,
  MAXIMO_TENTATIVAS,
  MontarTentativaLocal,
  PalavraFoiAcertada,
  ValidarPalavra,
} from "../../utils/logica-jogo.js";
import {
  LetrasPreenchidas,
  LetrasVazias,
  MontarPalavraChute,
  PalavraJaFoiTentada,
  RegistrarLetrasNoTeclado,
} from "../../utils/jogo.js";
import { LimparSessao, PersistirSessao } from "../../utils/sessao.js";
import {
  persistir,
  revelarTentativaSolo,
} from "./acoes-solo.js";
import { mostrarResultadoSolo } from "./acoes-resultado.js";

function GerarIdPartidaPratica() {
  return `local-pratica-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export async function iniciarPraticaLocal(cacheDicionarioSet) {
  let Conjunto = cacheDicionarioSet;
  if (!Conjunto?.size) {
    Conjunto = await GarantirCacheDicionario();
  }
  if (!Conjunto?.size) {
    this.mostrarToast(
      "Prática offline precisa do dicionário: conecte à internet, abra o menu e toque em «Limpar cache local» se já tentou antes; depois inicie a prática de novo.",
      true
    );
    return false;
  }

  const Secreta = EscolherPalavraAleatoria(Conjunto);
  if (!Secreta) {
    this.mostrarToast("Dicionário indisponível.", true);
    return false;
  }

  LimparSessao();
  this.iniciarTelaJogo("Prática");
  this.modo = "pratica";
  this.idPartida = GerarIdPartidaPratica();
  this.tokenPartida = null;
  this.dataDia = null;
  this.palavraSecreta = Secreta;
  this.maxTentativas = MAXIMO_TENTATIVAS;
  this.tabuleiros = null;
  persistir.call(this);
  this.fecharDialogs();
  return true;
}

export function restaurarPraticaLocal(salvoSolo) {
  if (!salvoSolo?.palavraSecreta) return false;
  this.modo = "pratica";
  this.idPartida = salvoSolo.idPartida;
  this.tokenPartida = null;
  this.palavraSecreta = salvoSolo.palavraSecreta;
  this.maxTentativas = salvoSolo.maximoTentativas || MAXIMO_TENTATIVAS;
  this.tentativa = salvoSolo.tentativa ?? 0;
  this.tentativasHist = salvoSolo.tentativasHist || [];
  this.teclado = { ...(salvoSolo.teclado || {}) };
  this.letras = Array.isArray(salvoSolo.letras)
    ? [...salvoSolo.letras]
    : LetrasVazias();
  this.indiceCursor =
    typeof salvoSolo.indiceCursor === "number"
      ? salvoSolo.indiceCursor
      : 0;
  this.encerrada = false;
  this.tabuleiros = null;
  this.gradesMulti = [];
  this.labelModo = "Prática";
  this.irParaView("jogo");
  return true;
}

export async function enviarChutePraticaLocal(cacheDicionarioSet) {
  if (!LetrasPreenchidas(this.letras)) {
    this.mostrarToast("Preencha as 5 letras", true);
    return;
  }
  const Palavra = MontarPalavraChute(this.letras);
  if (PalavraJaFoiTentada(Palavra, this.tentativasHist)) {
    this.tratarChuteInvalido("Você já tentou essa palavra.");
    return;
  }

  let Conjunto = cacheDicionarioSet;
  if (!Conjunto?.size) {
    Conjunto = await GarantirCacheDicionario();
  }
  if (!Conjunto?.size) {
    this.mostrarToast(
      "Dicionário offline indisponível. Conecte-se para atualizar.",
      true
    );
    return;
  }

  const Val = ValidarPalavra(
    Palavra,
    this.tentativasHist,
    Conjunto,
    this.dificuldade === "dificil"
  );
  if (!Val.valido) {
    this.tratarChuteInvalido(Val.mensagem);
    return;
  }

  if (!this.palavraSecreta) {
    this.mostrarToast("Partida inválida. Inicie uma nova prática.", true);
    return;
  }

  this.carregandoChute = true;
  try {
    const Tentativa = MontarTentativaLocal(this.palavraSecreta, Palavra);
    const Idx = this.tentativa;
    revelarTentativaSolo.call(this, Idx, Tentativa, true);
    this.teclado = RegistrarLetrasNoTeclado(Tentativa, this.teclado);
    this.tentativa++;
    this.letras = LetrasVazias();
    this.indiceCursor = 0;

    const Venceu = PalavraFoiAcertada(this.palavraSecreta, Palavra);
    const TentativasUsadas = this.tentativasHist.length;
    const Encerrada =
      Venceu || TentativasUsadas >= (this.maxTentativas || MAXIMO_TENTATIVAS);

    if (Venceu) TocarSom("acerto");
    else TocarSom("chute");

    if (Encerrada) {
      this.encerrada = true;
      LimparSessao();
      const PalavraFim = this.palavraSecreta;
      setTimeout(() => {
        if (Venceu) TocarSom("vitoria");
        mostrarResultadoSolo.call(
          this,
          Venceu,
          PalavraFim,
          null,
          "pratica",
          TentativasUsadas
        );
      }, DURACAO_FLIP_LINHA + 80);
    } else {
      persistir.call(this);
    }
  } finally {
    this.carregandoChute = false;
  }
}

export const acoesPraticaLocal = {
  iniciarPraticaLocal,
  restaurarPraticaLocal,
  enviarChutePraticaLocal,
};
