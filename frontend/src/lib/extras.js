/** Preferências, salas públicas, stats e sons. */
import { api } from "../services/api.js";

export function ObterPreferencias() {
  try {
    const P = JSON.parse(localStorage.getItem("termoPrefs") || "{}");
    if (P.som === undefined) P.som = true;
    if (P.volume === undefined) P.volume = 0.75;
    return P;
  } catch {
    return { som: true, volume: 0.75 };
  }
}

export function SalvarPreferencias(P) {
  localStorage.setItem("termoPrefs", JSON.stringify(P));
}

export { TocarSom, prepararSons, desbloquearAudio } from "./som.js";

export function AplicarDaltonismo(Ativo) {
  document.body.classList.toggle("modo-daltonico", !!Ativo);
}

export { AplicarTemaPreferencias as AplicarTema, ObservarTemaSistema } from "../utils/tema.js";

export function AplicarTemaLegado(claro) {
  document.documentElement.classList.toggle("tema-claro", !!claro);
}

export async function CarregarSalasPublicas(ListaEl) {
  if (!ListaEl) return;
  try {
    const D = await api.salasPublicas();
    const Salas = D.salas || [];
    if (!Salas.length) {
      ListaEl.innerHTML = '<li class="ranking-vazio">Nenhuma sala pública agora</li>';
      return;
    }
    ListaEl.innerHTML = Salas.map(
      (S) =>
        `<li><button type="button" class="btn-sala-publica" data-codigo="${S.codigoSala}">${S.codigoSala}</button> ${S.online}/${S.jogadores} · ${S.modoSessaoTexto}</li>`
    ).join("");
    ListaEl.querySelectorAll(".btn-sala-publica").forEach((B) => {
      B.addEventListener("click", () => {
        const Input = document.getElementById("inputCodigo");
        if (Input) Input.value = B.dataset.codigo;
      });
    });
  } catch {
    ListaEl.innerHTML = '<li class="ranking-vazio">Erro ao carregar salas</li>';
  }
}

export async function CarregarStatsServidor(Nick, El) {
  try {
    const D = await api.stats(Nick);
    if (El.taxa) El.taxa.textContent = `${D.taxaVitoria || 0}%`;
    if (El.extra) {
      El.extra.textContent = `${D.partidasRanking || 0} partidas no ranking · ${D.diariasVencidas || 0} diárias ganhas (14d)`;
    }
  } catch {
    /* ok */
  }
}

export async function CarregarHistoricoDiaria(_Nick, ListaEl) {
  if (!ListaEl) return;
  try {
    const D = await api.historicoDiaria();
    const H = D.historico || [];
    if (!H.length) {
      ListaEl.innerHTML = '<li class="ranking-vazio">Nenhuma diária salva ainda</li>';
      return;
    }
    ListaEl.innerHTML = H.map((Item) => {
      const Data = new Date(Item.dataDia + "T12:00:00").toLocaleDateString("pt-BR", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
      const Classe = Item.venceu ? "historico-ok" : "historico-falha";
      const Resultado = Item.venceu ? "Venceu" : "Não venceu";
      return `<li><span>${Data}</span><span class="${Classe}">${Resultado} · ${Item.tentativasUsadas} tent.</span></li>`;
    }).join("");
  } catch {
    ListaEl.innerHTML = '<li class="ranking-vazio">—</li>';
  }
}

export async function MontarFrasesChat(Container) {
  if (!Container) return;
  try {
    const D = await api.frasesChat();
    Container.innerHTML = (D.frases || []).map(
      (F) => `<button type="button" class="btn-chat-frase" data-frase="${F}">${F}</button>`
    ).join("");
  } catch {
    /* ok */
  }
}
