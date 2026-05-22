import { describe, it, expect } from "vitest";
import { TextoXpGanho, BarrasHistorico7d } from "./progresso.js";

describe("TextoXpGanho", () => {
  it("mostra cap diário", () => {
    expect(TextoXpGanho({ xpCapAtingido: true, xpGanho: 0 })).toContain("Limite diário");
  });

  it("mostra base e percentual", () => {
    const t = TextoXpGanho({
      xpGanho: 7,
      xpBruto: 10,
      multiplicadorXpPct: 70,
    });
    expect(t).toContain("+7 XP");
    expect(t).toContain("10 base");
    expect(t).toContain("70%");
  });
});

describe("BarrasHistorico7d", () => {
  it("monta barras", () => {
    const b = BarrasHistorico7d({
      dias: ["2026-05-15", "2026-05-16"],
      xp: [10, 0],
      deltaRp: [5, -3],
    });
    expect(b).toHaveLength(2);
    expect(b[0].alturaXp).toBe(100);
    expect(b[1].alturaXp).toBe(0);
  });
});
