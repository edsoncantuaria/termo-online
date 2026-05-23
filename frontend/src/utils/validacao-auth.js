/** Alinhado a `src/nucleo/contas.py` (NICK_RE). */

const NICK_RE = /^[a-z0-9_]{3,20}$/;

export function NormalizarNick(valor) {
  return (valor || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, "")
    .slice(0, 20);
}

export function ValidarNick(nickBruto) {
  const nick = NormalizarNick(nickBruto);
  if (!nick) {
    return {
      ok: false,
      nick: "",
      mensagem: "Informe um nome para jogar.",
    };
  }
  if (nick.length < 3) {
    return {
      ok: false,
      nick,
      mensagem: `Mínimo 3 caracteres (a–z, números ou _). Você tem ${nick.length}.`,
    };
  }
  if (!NICK_RE.test(nick)) {
    return {
      ok: false,
      nick,
      mensagem:
        "Nick inválido: use 3–20 caracteres (letras minúsculas, números ou _).",
    };
  }
  return { ok: true, nick, mensagem: "" };
}

export function ValidarLogin(identificador, senha) {
  const id = (identificador || "").trim();
  if (id.length < 3) {
    return { ok: false, mensagem: "Informe e-mail ou nick (mínimo 3 caracteres)." };
  }
  if (!senha || senha.length < 6) {
    return { ok: false, mensagem: "A senha precisa ter pelo menos 6 caracteres." };
  }
  return { ok: true, mensagem: "" };
}

export function ValidarRegistro(nick, email, senha, confirmarSenha) {
  const V = ValidarNick(nick);
  if (!V.ok) return V;
  const mail = (email || "").trim();
  if (mail.length < 5 || !mail.includes("@")) {
    return { ok: false, mensagem: "Informe um e-mail válido." };
  }
  if (!senha || senha.length < 6) {
    return { ok: false, mensagem: "A senha precisa ter pelo menos 6 caracteres." };
  }
  if (senha !== confirmarSenha) {
    return { ok: false, mensagem: "As senhas não coincidem." };
  }
  return { ok: true, nick: V.nick, mensagem: "" };
}
