import { describe, expect, it } from "vitest";
import { CalcularInstigacaoSerie } from "./instigacao-serie.js";

describe("CalcularInstigacaoSerie", () => {
  it("match point quando falta 1 vitória para você", () => {
    expect(
      CalcularInstigacaoSerie({ vitoriasEu: 1, vitoriasOpp: 0, meta: 2 })
    ).toMatchObject({
      tipo: "vantagem",
      texto: expect.stringContaining("vence a partida"),
    });
  });

  it("sobrevivência quando oponente está a 1 da vitória", () => {
    expect(
      CalcularInstigacaoSerie({ vitoriasEu: 0, vitoriasOpp: 1, meta: 2 })
    ).toMatchObject({
      tipo: "pressionado",
      texto: expect.stringContaining("continuar"),
    });
  });

  it("mapa decisivo em empate 1-1 (melhor de 3)", () => {
    expect(
      CalcularInstigacaoSerie({ vitoriasEu: 1, vitoriasOpp: 1, meta: 2 })
    ).toMatchObject({ tipo: "decisivo" });
  });

  it("sem mensagem no início 0-0", () => {
    expect(
      CalcularInstigacaoSerie({ vitoriasEu: 0, vitoriasOpp: 0, meta: 2 })
    ).toBeNull();
  });
});
