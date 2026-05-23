import { UrlApi } from "../config/origem.js";
import { HeadersAuth } from "../utils/auth.js";

function MensagemErroApi(corpo) {
  const detalhe = corpo?.detail;
  if (typeof detalhe === "string" && detalhe.trim()) return detalhe.trim();
  if (Array.isArray(detalhe) && detalhe.length) {
    return detalhe
      .map((item) => {
        if (typeof item === "string") return item;
        const msg = item?.msg || item?.message;
        if (msg) return String(msg);
        return null;
      })
      .filter(Boolean)
      .join(" ") || "Dados inválidos.";
  }
  if (corpo?.mensagem) return String(corpo.mensagem);
  return "Erro na requisição";
}

async function JsonOuErro(R) {
  const corpo = await R.json().catch(() => ({}));
  if (!R.ok) throw new Error(MensagemErroApi(corpo));
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
    fetchAuth(UrlApi(`/api/stats?nick=${encodeURIComponent(nick)}`)).then(
      JsonOuErro
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
    fetchAuth(UrlApi("/api/sala/criar"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(JsonOuErro),
  salaConvite: (codigo) =>
    fetch(UrlApi(`/api/sala/${encodeURIComponent(codigo)}/convite`)).then(
      JsonOuErro
    ),
  salaEntrar: (body) =>
    fetch(UrlApi("/api/sala/entrar"), {
      method: "POST",
      headers: HeadersAuth({ "Content-Type": "application/json" }),
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

  ranqueadaElos: () => fetch(UrlApi("/api/ranqueada/elos")).then((r) => r.json()),

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
