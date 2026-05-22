import { HeadersAuth } from "../utils/auth.js";

async function JsonOuErro(R) {
  const corpo = await R.json().catch(() => ({}));
  if (!R.ok) throw new Error(corpo.detail || corpo.mensagem || "Erro na requisição");
  return corpo;
}

function fetchAuth(url, opts = {}) {
  return fetch(url, {
    ...opts,
    headers: HeadersAuth(opts.headers || {}),
  });
}

export const api = {
  diariaInfo: (nick) =>
    fetchAuth(`/api/diaria/info?nick=${encodeURIComponent(nick)}`).then(JsonOuErro),
  diariaGrade: (body) =>
    fetchAuth("/api/diaria/grade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  dicionarioPalavras: () => fetch("/api/dicionario/palavras").then(JsonOuErro),
  stats: (nick) =>
    fetch(`/api/stats?nick=${encodeURIComponent(nick)}`).then((r) => r.json()),
  historicoDiaria: () => fetchAuth("/api/diaria/historico").then(JsonOuErro),
  salasPublicas: () => fetch("/api/salas/publicas").then((r) => r.json()),
  frasesChat: () => fetch("/api/arena/frases-chat").then((r) => r.json()),
  jogarIniciar: (body) =>
    fetchAuth("/api/jogar/iniciar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  jogarChute: (body) =>
    fetchAuth("/api/jogar/chute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  progressoEu: () => fetchAuth("/api/progresso/eu").then(JsonOuErro),
  jogarEstado: (id, tokenPartida) => {
    const q = tokenPartida
      ? `?tokenPartida=${encodeURIComponent(tokenPartida)}`
      : "";
    return fetchAuth(`/api/jogar/estado/${id}${q}`).then(JsonOuErro);
  },
  salaCriar: (body) =>
    fetch("/api/sala/criar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaEntrar: (body) =>
    fetch("/api/sala/entrar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaSair: (body) =>
    fetch("/api/sala/sair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  salaEstado: (codigo, idJogador) =>
    fetch(
      `/api/sala/${codigo}?id_jogador=${encodeURIComponent(idJogador)}`,
      { cache: "no-store" }
    ),
  desafioCriar: () =>
    fetch("/api/desafio/criar", { method: "POST" }).then(JsonOuErro),

  authRegistrar: (nick, email, senha) =>
    fetchAuth("/api/auth/registrar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nick, email, senha }),
    }).then(JsonOuErro),

  authLogin: (identificador, senha) =>
    fetchAuth("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identificador, senha }),
    }).then(JsonOuErro),

  authVisitante: (nick) =>
    fetchAuth("/api/auth/visitante", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nick: nick || null }),
    }).then(JsonOuErro),

  authEu: () => fetchAuth("/api/auth/eu").then(JsonOuErro),

  ranqueadaRanking: () => fetchAuth("/api/ranqueada/ranking").then(JsonOuErro),

  ranqueadaRevanche: () =>
    fetchAuth("/api/ranqueada/revanche", { method: "POST" }).then(JsonOuErro),

  ranqueadaElos: () => fetch("/api/ranqueada/elos").then((r) => r.json()),

  ranqueadaEntrarFila: () =>
    fetchAuth("/api/ranqueada/fila", { method: "POST" }).then(JsonOuErro),

  ranqueadaSairFila: () =>
    fetchAuth("/api/ranqueada/fila", { method: "DELETE" }).then(JsonOuErro),

  ranqueadaStatusFila: () => fetchAuth("/api/ranqueada/fila").then(JsonOuErro),
};
