/** Contagem até a próxima palavra do dia (meia-noite local). */

export function TextoProximaDiaria() {
  const agora = new Date();
  const proxima = new Date(agora);
  proxima.setHours(24, 0, 0, 0);
  const ms = proxima - agora;
  if (ms <= 0) return "Nova palavra em breve";
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  if (h > 0) return `Próxima palavra em ${h}h ${m}min`;
  return `Próxima palavra em ${m} min`;
}
