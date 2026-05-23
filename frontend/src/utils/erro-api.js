/** Mensagens de erro HTTP amigáveis (503, 429, corpo da API). */

export function MensagemErroApi(corpo) {
  const detalhe = corpo?.detail;
  if (typeof detalhe === "string" && detalhe.trim()) return detalhe.trim();
  if (Array.isArray(detalhe) && detalhe.length) {
    return (
      detalhe
        .map((item) => {
          if (typeof item === "string") return item;
          const msg = item?.msg || item?.message;
          if (msg) return String(msg);
          return null;
        })
        .filter(Boolean)
        .join(" ") || "Dados inválidos."
    );
  }
  if (corpo?.mensagem) return String(corpo.mensagem);
  return "";
}

export function MensagemErroHttp(resposta, corpo) {
  const base = MensagemErroApi(corpo);
  const retry = resposta.headers?.get?.("Retry-After");
  const seg = retry ? parseInt(retry, 10) : NaN;

  if (resposta.status === 503) {
    if (base) {
      return Number.isFinite(seg) && seg > 0
        ? `${base} Tente de novo em ${seg}s.`
        : base;
    }
    return Number.isFinite(seg) && seg > 0
      ? `Servidor ocupado. Tente de novo em ${seg} segundos.`
      : "Servidor ocupado. Aguarde um momento e tente de novo.";
  }
  if (resposta.status === 429) {
    if (base) {
      return Number.isFinite(seg) && seg > 0
        ? `${base} Aguarde ${seg}s.`
        : base;
    }
    return Number.isFinite(seg) && seg > 0
      ? `Muitas requisições. Aguarde ${seg} segundos.`
      : "Muitas requisições. Aguarde um instante.";
  }
  return base || "Erro na requisição";
}
