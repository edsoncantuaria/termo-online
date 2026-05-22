/** Contagem até a próxima palavra do dia (meia-noite em Brasília). */

import { MsAteProximaMeiaNoiteBrasil } from "./tempo-brasil.js";

export function TextoProximaDiaria() {
  const ms = MsAteProximaMeiaNoiteBrasil();
  if (ms <= 0) return "Nova palavra em breve";
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  if (h > 0) return `Próxima palavra em ${h}h ${m}min`;
  return `Próxima palavra em ${m} min`;
}
