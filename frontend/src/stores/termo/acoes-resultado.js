/** Diálogos e persistência de resultados (solo e arena). */
import { api } from "../../services/api.js";
import { SalvarAuthLocal } from "../../utils/auth.js";
import { ModoVitoriasArena } from "../../utils/jogo.js";
import { GerarTextoCompartilhar, MontarResultadoUi } from "../../utils/jogo.js";
import { ObterStats, SalvarStats } from "../../utils/stats.js";
import { LimparSessao } from "../../utils/sessao.js";
import { ClasseElo, NOMES_ELO } from "../../utils/elos.js";

export function mostrarResultadoSolo(venceu, palavra, pontos, modo, tentativasUsadas) {
  const tentativa =
    tentativasUsadas ?? this.tentativa ?? this.tentativasHist.length;
  const gradeTexto = GerarTextoCompartilhar({
    modo,
    tentativa,
    maxTentativas: this.maxTentativas,
    tentativasHist: this.tentativasHist,
    dataDia: this.dataDia,
    codigoSala: this.codigoSala,
    venceu,
  });
  this.resultado = MontarResultadoUi({
    modo,
    venceu,
    tentativa,
    maxTentativas: this.maxTentativas,
    gradeTexto,
    pontos,
    palavra,
    dataDia: this.dataDia,
  });
  if (modo === "diaria") {
    const S = ObterStats();
    S.ultimaGrade = gradeTexto;
    SalvarStats(S);
    this.statsLocais = S;
    api
      .diariaGrade({
        nick: this.nickJogo,
        gradeTexto,
        venceu,
        tentativasUsadas: this.tentativa,
        pontos: typeof pontos === "number" ? pontos : 0,
      })
      .catch(() => {});
    this.carregarInfoDiaria();
  }
  if (modo === "arena" && venceu) {
    const S = ObterStats();
    S.vitorias = (S.vitorias || 0) + 1;
    S.sequencia = (S.sequencia || 0) + 1;
    SalvarStats(S);
    this.statsLocais = S;
  }
  this.atualizarStatsUI();
  if (modo === "pratica" || modo === "diaria") LimparSessao();
  this.abrirDialog("resultado");
}

export function mostrarResultadoArena(D, venci, campeao) {
  const ehRanq = this.modo === "ranqueada" || D.configuracao?.ranqueada;
  const porVitorias = ModoVitoriasArena(D);
  const meta = ehRanq ? D.metaVitorias || 2 : D.metaVitorias || 5;
  const meuPlacar = D.placar?.find((j) => j.idJogador === this.idJogador);
  const meuRanq = (D.resultadosRanqueada || []).find(
    (r) => r.idConta && r.idConta === this.conta?.idConta
  );
  const partidasAntes = this.conta?.partidasRanqueadas || 0;
  const vitoriasAntes = this.conta?.vitoriasRanqueadas || 0;
  const vitoriasTotais = vitoriasAntes + (ehRanq && venci ? 1 : 0);
  const partidasTotais = partidasAntes + (ehRanq ? 1 : 0);
  const derrotasTotais = Math.max(0, partidasTotais - vitoriasTotais);
  const placarSerie = (D.placar || [])
    .map((j) => `${j.vitoriasRodada || 0}`)
    .join("–");
  const linhas = (D.placar || [])
    .map((j, i) =>
      porVitorias
        ? `${i + 1}. ${j.nomeJogador} — ${j.vitoriasRodada || 0}/${meta} vit.`
        : `${i + 1}. ${j.nomeJogador} — ${j.pontosAcumulados} pts`
    )
    .join("\n");
  const gradeTexto = ehRanq
    ? `Termo Ranqueado · melhor de 3\nSérie ${placarSerie}\n\n${linhas}`
    : `Termo Arena ${D.codigoSala}\nRodadas: ${D.rodadaAtual}\n\n${linhas}`;
  this.resultado = {
    titulo: ehRanq
      ? venci
        ? "Vitória no ranqueado!"
        : "Derrota no ranqueado"
      : venci
        ? "Você venceu a sessão!"
        : "Sessão encerrada",
    texto: campeao
      ? ehRanq
        ? `Melhor de 3 — ${campeao.nomeJogador} venceu a série (${campeao.vitoriasRodada || 0} mapas).`
        : porVitorias
          ? `Campeão: ${campeao.nomeJogador} com ${campeao.vitoriasRodada || 0} vitórias (meta ${meta}).`
          : `Campeão: ${campeao.nomeJogador} com ${campeao.pontosAcumulados} pontos.`
      : "Obrigado por jogar!",
    pontos: "",
    ranqueadaResumo: meuRanq
      ? {
          delta: meuRanq.delta,
          pontosAntes: meuRanq.pontosAntes,
          pontosDepois: meuRanq.pontosDepois,
          eloDepois: meuRanq.eloDepois,
          venceu: venci,
          vitorias: vitoriasTotais,
          derrotas: derrotasTotais,
          placarSerie,
        }
      : null,
    confete: venci,
    gradeTexto,
    mostrarGrade: !ehRanq,
    mostrarCopiar: !ehRanq,
    mostrarCompartilhar: !ehRanq,
    mostrarRevanche: !!(this.souCriador && this.codigoSala),
    mostrarRevancheRanqueada: !!(ehRanq && D.revancheRanqueada?.disponivel),
    revancheOponenteNick: D.revancheRanqueada?.oponenteNick || "",
  };
  if (venci) {
    const S = ObterStats();
    S.vitorias = (S.vitorias || 0) + 1;
    S.sequencia = (S.sequencia || 0) + 1;
    SalvarStats(S);
    this.statsLocais = S;
  }
  if (meuRanq && this.conta) {
    const EloId = meuRanq.eloDepois;
    const Nome = NOMES_ELO[EloId] || EloId;
    this.conta = {
      ...this.conta,
      pontosRanqueada: meuRanq.pontosDepois,
      elo: EloId,
      eloNome: Nome,
      rotuloRank: Nome,
      semRank: false,
      eloClasse: ClasseElo(EloId),
      partidasRanqueadas: partidasTotais,
      partidasTemporada: (this.conta.partidasTemporada || 0) + 1,
      vitoriasRanqueadas: vitoriasTotais,
      vitoriasTemporada: (this.conta.vitoriasTemporada || 0) + (venci ? 1 : 0),
    };
    SalvarAuthLocal(this.token, this.conta);
    this.carregarRankingRanqueado();
    api
      .progressoEu()
      .then((p) => {
        this.conta = { ...this.conta, progresso: p };
        SalvarAuthLocal(this.token, this.conta);
      })
      .catch(() => {});
  }
  this.atualizarStatsUI();
  this.abrirDialog("resultado");
}

export const acoesResultado = {
  mostrarResultadoSolo,
  mostrarResultadoArena,
};
