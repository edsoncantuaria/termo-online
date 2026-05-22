/** Datas e contagem no fuso America/Sao_Paulo (palavra do dia). */

export function DataHojeIsoBrasil() {
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: "America/Sao_Paulo",
  }).format(new Date());
}

/** Milissegundos até a próxima meia-noite em Brasília. */
export function MsAteProximaMeiaNoiteBrasil() {
  const agora = Date.now();
  const Partes = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Sao_Paulo",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
    hour12: false,
  }).formatToParts(new Date());
  const H = Number(Partes.find((p) => p.type === "hour")?.value || 0);
  const M = Number(Partes.find((p) => p.type === "minute")?.value || 0);
  const S = Number(Partes.find((p) => p.type === "second")?.value || 0);
  const Decorridos = (H * 3600 + M * 60 + S) * 1000;
  return 86400000 - Decorridos;
}
