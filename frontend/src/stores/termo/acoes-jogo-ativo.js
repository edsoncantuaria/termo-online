/** Jogo ativo na home: reconectar, abandonar, voltar sem sair da partida. */
import { api } from "../../services/api.js";
import { EhModoSalaOnline } from "../../utils/modos.js";
import { JogoAtivoDeSessaoLocal } from "../../utils/jogo-ativo.js";
import { ObterSessao, LimparSessao, PersistirSessao } from "../../utils/sessao.js";
import { DiariaJaJogadaLocal } from "../../utils/stats.js";
import { entrarSalaRanqueada } from "./acoes-ranqueada.js";

export async function carregarJogoAtivo() {
  if (this.conta?.idConta && !this.conta?.ehVisitante) {
    try {
      const D = await api.contaJogoAtivo();
      this.jogoAtivo = D?.ativo ? D : null;
      return;
    } catch {
      this.jogoAtivo = null;
    }
  } else {
    this.jogoAtivo = JogoAtivoDeSessaoLocal(ObterSessao());
  }
}

export async function reconectarJogoAtivo() {
  const J = this.jogoAtivo;
  if (!J?.ativo || this.carregandoJogoAtivo) return;

  this.carregandoJogoAtivo = true;
  try {
    if (J.tipo === "ranqueada") {
      await entrarSalaRanqueada.call(this, J);
    } else if (J.tipo === "arena") {
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
      if (estado.partidaEncerrada) throw new Error("Partida já encerrada.");
      this.entrarNaSala(estado);
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
          ? "Você perderá o duelo ranqueado e os pontos serão aplicados."
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
        await carregarJogoAtivo.call(this);
      } finally {
        this.carregandoJogoAtivo = false;
      }
    },
  });
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
  reconectarJogoAtivo,
  abandonarJogoAtivo,
  voltarInicioPreservandoPartida,
};
