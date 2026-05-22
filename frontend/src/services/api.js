import { UrlApi } from "../config/origem.js";
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
    fetchAuth(UrlApi(`/api/diaria/info?nick=${encodeURIComponent(nick)}`)).then(
      JsonOuErro
    ),
  diariaGrade: (body) =>
    fetchAuth(UrlApi("/api/diaria/grade"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  dicionarioPalavras: () => fetch(UrlApi("/api/dicionario/palavras")).then(JsonOuErro),
  stats: (nick) =>
    fetch(UrlApi(`/api/stats?nick=${encodeURIComponent(nick)}`)).then((r) =>
      r.json()
    ),
  historicoDiaria: () => fetchAuth(UrlApi("/api/diaria/historico")).then(JsonOuErro),
  salasPublicas: () => fetch(UrlApi("/api/salas/publicas")).then((r) => r.json()),
  frasesChat: () => fetch(UrlApi("/api/arena/frases-chat")).then((r) => r.json()),
  jogarIniciar: (body) =>
    fetchAuth(UrlApi("/api/jogar/iniciar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  jogarChute: (body) =>
    fetchAuth(UrlApi("/api/jogar/chute"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  progressoEu: () => fetchAuth(UrlApi("/api/progresso/eu")).then(JsonOuErro),
  jogarEstado: (id, tokenPartida) => {
    const q = tokenPartida
      ? `?tokenPartida=${encodeURIComponent(tokenPartida)}`
      : "";
    return fetchAuth(UrlApi(`/api/jogar/estado/${id}${q}`)).then(JsonOuErro);
  },
  salaCriar: (body) =>
    fetch(UrlApi("/api/sala/criar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaEntrar: (body) =>
    fetch(UrlApi("/api/sala/entrar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaSair: (body) =>
    fetch(UrlApi("/api/sala/sair"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  salaEstado: (codigo, idJogador) =>
    fetch(
      UrlApi(`/api/sala/${codigo}?id_jogador=${encodeURIComponent(idJogador)}`),
      { cache: "no-store" }
    ),
  desafioCriar: () =>
    fetch(UrlApi("/api/desafio/criar"), { method: "POST" }).then(JsonOuErro),

  authRegistrar: (nick, email, senha) =>
    fetchAuth(UrlApi("/api/auth/registrar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nick, email, senha }),
    }).then(JsonOuErro),

  authLogin: (identificador, senha) =>
    fetchAuth(UrlApi("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identificador, senha }),
    }).then(JsonOuErro),

  authVisitante: (nick) =>
    fetchAuth(UrlApi("/api/auth/visitante"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nick: nick || null }),
    }).then(JsonOuErro),

  authEu: () => fetchAuth(UrlApi("/api/auth/eu")).then(JsonOuErro),

  authAtualizarAvatar: (avatarId) =>
    fetchAuth(UrlApi("/api/auth/avatar"), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ avatarId }),
    }).then(JsonOuErro),

  ranqueadaRanking: () =>
    fetchAuth(UrlApi("/api/ranqueada/ranking")).then(JsonOuErro),

  ranqueadaRevanche: () =>
    fetchAuth(UrlApi("/api/ranqueada/revanche"), { method: "POST" }).then(
      JsonOuErro
    ),

  ranqueadaElos: () => fetch(UrlApi("/api/ranqueada/elos")).then((r) => r.json()),

  ranqueadaEntrarFila: () =>
    fetchAuth(UrlApi("/api/ranqueada/fila"), { method: "POST" }).then(JsonOuErro),

  ranqueadaSairFila: () =>
    fetchAuth(UrlApi("/api/ranqueada/fila"), { method: "DELETE" }).then(JsonOuErro),

  ranqueadaStatusFila: () =>
    fetchAuth(UrlApi("/api/ranqueada/fila")).then(JsonOuErro),
};
