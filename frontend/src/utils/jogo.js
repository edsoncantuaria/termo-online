import { TAMANHO_PALAVRA } from "./constantes.js";
import { DataHojeIsoBrasil } from "./tempo-brasil.js";

export function PrioridadeTeclado(a, b) {
  const ordem = { correto: 3, presente: 2, ausente: 1 };
  return (ordem[a] || 0) > (ordem[b] || 0) ? a : b;
}

export function NormalizarTentativa(Tent) {
  if (!Tent) return { letras: [], estados: [] };
  let letras = Tent.letras;
  if (!letras || letras.length !== TAMANHO_PALAVRA) {
    const fonte = (Tent.palavra || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
    letras = [...fonte.toUpperCase()].slice(0, TAMANHO_PALAVRA);
    while (letras.length < TAMANHO_PALAVRA) letras.push("");
  }
  return { ...Tent, letras, estados: Tent.estados || [] };
}

export function ContarVerdesTentativa(Tent) {
  const t = NormalizarTentativa(Tent);
  return (t.estados || []).filter((e) => e === "correto").length;
}

/** Melhor tentativa para comparar adversários (mais letras verdes). */
export function MelhorTentativaParaExibir(Tentativas) {
  if (!Tentativas?.length) return null;
  let Melhor = Tentativas[0];
  let MaxVerdes = ContarVerdesTentativa(Melhor);
  for (const T of Tentativas) {
    const V = ContarVerdesTentativa(T);
    if (V > MaxVerdes) {
      MaxVerdes = V;
      Melhor = T;
    }
  }
  return NormalizarTentativa(Melhor);
}

export function RegistrarLetrasNoTeclado(Tent, teclado) {
  const t = NormalizarTentativa(Tent);
  const novo = { ...teclado };
  t.letras.forEach((L, i) => {
    const k = (L || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
    if (k) novo[k] = PrioridadeTeclado(t.estados[i], novo[k]);
  });
  return novo;
}

export function LetrasVazias() {
  return Array(TAMANHO_PALAVRA).fill("");
}

export function NormalizarLetrasProgresso(Letras) {
  const L = Array.isArray(Letras) ? [...Letras] : [];
  while (L.length < TAMANHO_PALAVRA) L.push("");
  return L.slice(0, TAMANHO_PALAVRA).map((C) =>
    (C || "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .slice(0, 1)
  );
}

export function LetrasPreenchidas(Letras) {
  return NormalizarLetrasProgresso(Letras).every((C) => !!C);
}

export function MontarPalavraChute(Letras) {
  return NormalizarLetrasProgresso(Letras).join("");
}

export function PalavraDeTentativa(Tent) {
  const t = NormalizarTentativa(Tent);
  return MontarPalavraChute(t.letras);
}

function _LetrasTentativaOuLinha(tent, linha) {
  const fonte = linha || tent;
  let letras = [...(fonte.letras || [])];
  if (letras.length !== TAMANHO_PALAVRA && fonte.palavra) {
    const p = fonte.palavra
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
    letras = [...p].slice(0, TAMANHO_PALAVRA);
  }
  while (letras.length < TAMANHO_PALAVRA) letras.push("");
  return letras.map((c) =>
    (c || "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .slice(0, 1)
  );
}

function _ValidarVerdesDificil(letras, estados, letrasTent) {
  for (let i = 0; i < TAMANHO_PALAVRA; i++) {
    if (estados[i] === "correto" && letrasTent[i] && letras[i] !== letrasTent[i]) {
      return {
        ok: false,
        msg: `A letra '${letrasTent[i].toUpperCase()}' deve ficar na posição ${i + 1}.`,
      };
    }
  }
  return { ok: true, msg: null };
}

/** Modo difícil (feedback no cliente; servidor revalida). */
export function ValidarModoDificilClient(palavra, tentativasAnteriores) {
  const letras = MontarPalavraChute([...palavra]).split("");
  for (const tent of tentativasAnteriores || []) {
    if (tent.linhas?.length) {
      for (const linha of tent.linhas) {
        if (linha.venceu || !linha.estados?.length) continue;
        const letrasTent = _LetrasTentativaOuLinha(tent, linha);
        const r = _ValidarVerdesDificil(letras, linha.estados, letrasTent);
        if (!r.ok) return r;
      }
      continue;
    }
    const estados = tent.estados || [];
    if (!estados.length) continue;
    const letrasTent = _LetrasTentativaOuLinha(tent);
    const r = _ValidarVerdesDificil(letras, estados, letrasTent);
    if (!r.ok) return r;
  }
  return { ok: true, msg: null };
}

export function PalavraJaFoiTentada(palavra, tentativas) {
  const alvo = MontarPalavraChute(
    [...(palavra || "")].map((c) => c.toLowerCase())
  );
  if (!alvo || alvo.length !== TAMANHO_PALAVRA) return false;
  return (tentativas || []).some(
    (t) => PalavraDeTentativa(t) === alvo
  );
}

export function ProximoIndiceVazio(Letras, Inicio = 0) {
  const L = NormalizarLetrasProgresso(Letras);
  for (let I = 0; I < TAMANHO_PALAVRA; I++) {
    const Idx = (Inicio + I) % TAMANHO_PALAVRA;
    if (!L[Idx]) return Idx;
  }
  return Math.min(Inicio, TAMANHO_PALAVRA - 1);
}

export function LetrasEmProgressoSalvas(SalvoSolo) {
  const L = SalvoSolo?.letras;
  if (!Array.isArray(L)) return LetrasVazias();
  if (L.length > TAMANHO_PALAVRA && L.every((C) => !C)) return LetrasVazias();
  return NormalizarLetrasProgresso(L);
}

export function FormatarCronometro(Segundos) {
  const s = Math.max(0, Segundos);
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

export function ModoVitoriasArena(D) {
  return (D?.modoSessao || D?.configuracao?.modoSessao) === "vitorias";
}

export function FormatarDataDiaria(DataIso) {
  if (!DataIso) return "Hoje";
  const D = new Date(`${DataIso}T12:00:00`);
  if (Number.isNaN(D.getTime())) return DataIso;
  return D.toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export function EmojiEstadoParaTile(C) {
  if (C === "🟩") return "correto";
  if (C === "🟨") return "presente";
  return "ausente";
}

export function ParsearLinhaGradeEmoji(Linha) {
  const L = (Linha || "").trim();
  if (!L) return [];
  return [...L]
    .filter((C) => "🟩🟨⬛".includes(C))
    .map((C) => ({ tipo: EmojiEstadoParaTile(C) }));
}

/** Interpreta o texto salvo para copiar/compartilhar (formato legado ou novo). */
export function ParsearGradeCompartilhar(Texto) {
  const Partes = (Texto || "").trim().split("\n");
  const LinhaMeta = (Partes[0] || "").trim();
  const LinhasGrade = Partes
    .slice(1)
    .map((L) => L.trim())
    .filter((L) => /[🟩🟨⬛]/.test(L));

  let modo = "termo";
  if (/diária|diaria/i.test(LinhaMeta)) modo = "diaria";
  else if (/prática|pratica/i.test(LinhaMeta)) modo = "pratica";
  else if (/arena/i.test(LinhaMeta)) modo = "arena";

  const DataMatch = LinhaMeta.match(/\d{4}-\d{2}-\d{2}/);
  const dataDia = DataMatch ? DataMatch[0] : "";
  const ScoreMatch = LinhaMeta.match(/(\d+)\s*\/\s*(\d+)/);
  let tentativasUsadas = null;
  let maxTentativas = 6;
  let venceu = null;
  if (ScoreMatch) {
    tentativasUsadas = Number(ScoreMatch[1]);
    maxTentativas = Number(ScoreMatch[2]);
    venceu = true;
  } else if (/\bX\b/i.test(LinhaMeta)) {
    venceu = false;
  }

  const grade = LinhasGrade.map((L) => ParsearLinhaGradeEmoji(L));

  return {
    modo,
    dataDia,
    dataFormatada: FormatarDataDiaria(dataDia),
    tentativasUsadas,
    maxTentativas,
    venceu,
    grade,
    linhaMeta: LinhaMeta,
  };
}

export function GerarTextoCompartilhar({
  modo,
  tentativa,
  maxTentativas,
  tentativasHist,
  dataDia,
  codigoSala,
  venceu,
}) {
  const emoji = (e) =>
    e === "correto" ? "🟩" : e === "presente" ? "🟨" : "⬛";
  const linhas = tentativasHist.map((T) => {
    if (T.linhas) {
      return T.linhas
        .filter((L) => L.estados?.length)
        .map((L) => L.estados.map(emoji).join(""))
        .join(" ");
    }
    return (T.estados || []).map(emoji).join("");
  });
  const titulos = {
    diaria: "Termo Diária",
    pratica: "Termo Prática",
    arena: "Termo Arena",
  };
  const titulo = titulos[modo] || "Termo";
  const dataFmt = dataDia || DataHojeIsoBrasil();
  const score = venceu ? `${tentativa}/${maxTentativas}` : "X";
  const extra = modo === "arena" && codigoSala ? ` Sala ${codigoSala}` : "";
  return `${titulo}${extra} ${dataFmt} ${score}\n\n${linhas.join("\n")}`;
}

export function MontarResultadoUi({
  modo,
  venceu,
  tentativa,
  maxTentativas,
  gradeTexto,
  pontos,
  palavra,
  dataDia,
  mostrarRevanche = false,
}) {
  const ehDiaria = modo === "diaria";
  const dataFormatada = FormatarDataDiaria(dataDia || null);
  let titulo = venceu ? "Incrível!" : "Quase lá";
  let texto = venceu
    ? `Você acertou em ${tentativa} tentativa${tentativa === 1 ? "" : "s"}.`
    : palavra
      ? `A palavra era ${String(palavra).toUpperCase()}.`
      : "Não foi desta vez — tente de novo em outro modo.";

  if (ehDiaria) {
    titulo = venceu ? "Palavra do dia — acertou!" : "Palavra do dia — amanhã tem mais";
    texto = venceu
      ? `${dataFormatada} · ${tentativa}/${maxTentativas} tentativas`
      : `${dataFormatada} · volte amanhã para uma palavra nova.`;
  }

  const pode =
    ehDiaria ||
    modo === "pratica" ||
    modo === "arena" ||
    modo === "dueto" ||
    modo === "quarteto" ||
    modo === "desafio";

  return {
    titulo,
    texto,
    pontos: pontos ? `${pontos} pontos` : "",
    confete: venceu,
    confeteIntenso: venceu && ehDiaria,
    gradeTexto,
    mostrarGrade: pode && !!gradeTexto,
    mostrarCopiar: pode && !!gradeTexto,
    mostrarCompartilhar: pode && !!gradeTexto,
    mostrarRevanche,
    ehDiaria,
    modo,
    venceu,
    tentativasUsadas: tentativa,
    maxTentativas,
    dataDia: dataDia || null,
    dataFormatada,
  };
}

export function EhErroNick(Mensagem) {
  const m = (Mensagem || "").toLowerCase();
  return m.includes("nick") && (m.includes("sala") || m.includes("já") || m.includes("ja"));
}
