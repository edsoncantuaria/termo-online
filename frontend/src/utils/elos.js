/** Elos ranqueados — manter alinhado com src/nucleo/ranqueada.py (CORES_ELO). */

export const ROTULO_SEM_RANK = "Sem Rank";

export const NOMES_ELO = {
  papelao: "Papelão",
  madeira: "Madeira",
  ferro: "Ferro",
  bronze: "Bronze",
  prata: "Prata",
  ouro: "Ouro",
  platina: "Platina",
  diamante: "Diamante",
  estrela: "Estrela",
};

export const CORES_ELO = {
  papelao: {
    fundo: "linear-gradient(135deg, #6b5344 0%, #4a3828 100%)",
    texto: "#f5e6d3",
    borda: "rgba(180, 140, 90, 0.55)",
    brilho: "0 0 12px rgba(120, 90, 50, 0.35)",
  },
  madeira: {
    fundo: "linear-gradient(135deg, #8b5a2b 0%, #5c3d1e 100%)",
    texto: "#ffe8c8",
    borda: "rgba(210, 150, 80, 0.5)",
    brilho: "0 0 14px rgba(160, 100, 40, 0.4)",
  },
  ferro: {
    fundo: "linear-gradient(135deg, #8a939e 0%, #5a626c 100%)",
    texto: "#eef2f6",
    borda: "rgba(180, 190, 200, 0.45)",
    brilho: "0 0 10px rgba(140, 150, 160, 0.35)",
  },
  bronze: {
    fundo: "linear-gradient(135deg, #c97b3d 0%, #8b4513 100%)",
    texto: "#fff4e6",
    borda: "rgba(230, 160, 80, 0.55)",
    brilho: "0 0 16px rgba(200, 120, 40, 0.45)",
  },
  prata: {
    fundo: "linear-gradient(135deg, #e8ecef 0%, #9aa3ad 50%, #c5cdd6 100%)",
    texto: "#1a2230",
    borda: "rgba(220, 228, 235, 0.7)",
    brilho: "0 0 18px rgba(200, 210, 225, 0.5)",
  },
  ouro: {
    fundo: "linear-gradient(135deg, #ffe566 0%, #d4a017 45%, #b8860b 100%)",
    texto: "#2a1f08",
    borda: "rgba(255, 220, 100, 0.65)",
    brilho: "0 0 20px rgba(255, 200, 60, 0.55)",
  },
  platina: {
    fundo: "linear-gradient(135deg, #f0f8ff 0%, #7eb8da 40%, #4a7fa8 100%)",
    texto: "#0d1a28",
    borda: "rgba(180, 220, 255, 0.6)",
    brilho: "0 0 22px rgba(120, 180, 255, 0.5)",
  },
  diamante: {
    fundo: "linear-gradient(135deg, #e0ffff 0%, #5ec8e8 35%, #2a8fc4 70%, #7b68ee 100%)",
    texto: "#061820",
    borda: "rgba(150, 230, 255, 0.7)",
    brilho: "0 0 24px rgba(100, 200, 255, 0.6)",
  },
  estrela: {
    fundo: "linear-gradient(135deg, #fff9c4 0%, #ffd54f 25%, #ff6f00 55%, #7b1fa2 100%)",
    texto: "#fffef5",
    borda: "rgba(255, 220, 120, 0.75)",
    brilho:
      "0 0 28px rgba(255, 180, 50, 0.65), 0 0 40px rgba(180, 80, 255, 0.35)",
  },
};

export const ORDEM_ELOS = [
  "papelao",
  "madeira",
  "ferro",
  "bronze",
  "prata",
  "ouro",
  "platina",
  "diamante",
  "estrela",
];

export function ClasseElo(eloId) {
  if (!eloId) return "elo-pill--sem-rank";
  return `elo-pill--${eloId}`;
}

export function IndiceElo(eloId) {
  if (!eloId) return -1;
  return ORDEM_ELOS.indexOf(eloId);
}

/** True se a faixa de elo subiu após o duelo (ex.: Bronze → Prata). */
export function SubiuDeElo(eloAntes, eloDepois) {
  const ia = IndiceElo(eloAntes);
  const id = IndiceElo(eloDepois);
  return ia >= 0 && id > ia;
}

/** True se a faixa de elo caiu após o duelo (ex.: Prata → Bronze). */
export function CaiuDeElo(eloAntes, eloDepois) {
  const ia = IndiceElo(eloAntes);
  const id = IndiceElo(eloDepois);
  return ia >= 0 && id >= 0 && id < ia;
}

export function RotuloRankDeJogador(j) {
  if (j?.rotuloRank) return j.rotuloRank;
  if (j?.semRank) return ROTULO_SEM_RANK;
  return j?.eloNome || ROTULO_SEM_RANK;
}

export function EstiloInlineElo(eloId) {
  if (!eloId || !CORES_ELO[eloId]) return null;
  const C = CORES_ELO[eloId];
  return {
    background: C.fundo,
    color: C.texto,
    borderColor: C.borda,
    boxShadow: C.brilho,
  };
}
