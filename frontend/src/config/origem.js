/** Origem da API/WS em produção (ex.: https://api-termo.cloudive.com.br). Vazio = mesmo host. */
const Bruto = (import.meta.env.VITE_API_ORIGIN || "").trim().replace(/\/$/, "");

export function OrigemApi() {
  if (Bruto) return Bruto;
  if (typeof window !== "undefined") return window.location.origin;
  return "";
}

export function UrlApi(caminho) {
  const base = OrigemApi();
  const path = caminho.startsWith("/") ? caminho : `/${caminho}`;
  return base ? `${base}${path}` : path;
}

export function UrlWebSocket(caminho) {
  const base = OrigemApi() || (typeof window !== "undefined" ? window.location.origin : "");
  const u = new URL(base);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  const path = caminho.startsWith("/") ? caminho : `/${caminho}`;
  return `${u.origin}${path}`;
}
