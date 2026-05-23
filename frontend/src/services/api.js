import { UrlApi } from "../config/origem.js";
import { HeadersAuth } from "../utils/auth.js";
import { MensagemErroHttp } from "../utils/erro-api.js";

export async function fetchPublicoJson(url, opts = {}) {
  const R = await fetch(url, opts);
  return JsonOuErro(R);
}

async function JsonOuErro(R) {
  const corpo = await R.json().catch(() => ({}));
  if (!R.ok) {
    const E = new Error(MensagemErroHttp(R, corpo));
    E.status = R.status;
    throw E;
  }
  return corpo;
}

function fetchAuth(url, opts = {}) {
  return fetch(url, {
    ...opts,
    headers: HeadersAuth(opts.headers || {}),
  });
}

export function fetchAuthJson(url, opts = {}) {
  return fetchAuth(url, opts).then(JsonOuErro);
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
  tempo: () => fetchPublicoJson(UrlApi("/api/tempo")),
  dicionarioPalavras: () =>
    fetchPublicoJson(UrlApi("/api/dicionario/palavras")),
  stats: (nick) =>
    fetchAuth(UrlApi(`/api/stats?nick=${encodeURIComponent(nick)}`)).then(
      JsonOuErro
    ),
  historicoDiaria: () => fetchAuth(UrlApi("/api/diaria/historico")).then(JsonOuErro),
  salasPublicas: () => fetchPublicoJson(UrlApi("/api/salas/publicas")),
  frasesChat: () => fetchPublicoJson(UrlApi("/api/arena/frases-chat")),
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
    fetchAuth(UrlApi("/api/sala/criar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaConvite: (codigo) =>
    fetchPublicoJson(UrlApi(`/api/sala/${encodeURIComponent(codigo)}/convite`)),
  salaEntrar: (body) =>
    fetchPublicoJson(UrlApi("/api/sala/entrar"), {
      method: "POST",
      headers: HeadersAuth({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }),
  salaSair: (body) =>
    fetchPublicoJson(UrlApi("/api/sala/sair"), {
      method: "POST",
      headers: HeadersAuth({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }),
  salaEstado: (codigo, idJogador) =>
    fetchAuthJson(
      UrlApi(
        `/api/sala/${codigo}?id_jogador=${encodeURIComponent(idJogador)}`
      ),
      { cache: "no-store" }
    ),
  salaChute: (codigo, body) =>
    fetchAuthJson(UrlApi(`/api/sala/${encodeURIComponent(codigo)}/chute`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  partidaRetomar: (idPartida, tokenSessao, idJogador) => {
    const params = new URLSearchParams();
    if (tokenSessao) params.set("token", tokenSessao);
    if (idJogador) params.set("id_jogador", idJogador);
    const q = params.toString() ? `?${params}` : "";
    return fetchAuth(UrlApi(`/api/partida/${idPartida}/retomar${q}`)).then(
      JsonOuErro
    );
  },
  partidaDesistir: (idPartida, body) =>
    fetchAuth(UrlApi(`/api/partida/${idPartida}/desistir`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  desafioCriar: () =>
    fetchAuth(UrlApi("/api/desafio/criar"), { method: "POST" }).then(JsonOuErro),

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

  contaJogoAtivo: () =>
    fetchAuth(UrlApi("/api/conta/jogo-ativo")).then(JsonOuErro),

  contaUltimasPartidas: () =>
    fetchAuth(UrlApi("/api/conta/ultimas-partidas")).then(JsonOuErro),

  jogadorPerfil: (nick) =>
    fetchAuth(UrlApi(`/api/jogador/${encodeURIComponent(nick)}/perfil`)).then(
      JsonOuErro
    ),

  contaLimparJogoAtivo: () =>
    fetchAuth(UrlApi("/api/conta/jogo-ativo"), { method: "DELETE" }).then(
      JsonOuErro
    ),

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

  ranqueadaElos: () => fetchPublicoJson(UrlApi("/api/ranqueada/elos")),

  ranqueadaEntrarFila: (treino = false) =>
    fetchAuth(UrlApi("/api/ranqueada/fila"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ treino: !!treino }),
    }).then(JsonOuErro),

  ranqueadaHistorico: (limite = 20) =>
    fetchAuth(UrlApi(`/api/ranqueada/historico?limite=${limite}`)).then(JsonOuErro),

  ranqueadaTemporada: () =>
    fetchAuth(UrlApi("/api/ranqueada/temporada")).then(JsonOuErro),

  ranqueadaSairFila: () =>
    fetchAuth(UrlApi("/api/ranqueada/fila"), { method: "DELETE" }).then(JsonOuErro),

  ranqueadaStatusFila: () =>
    fetchAuth(UrlApi("/api/ranqueada/fila")).then(JsonOuErro),
};
