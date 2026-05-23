import { describe, expect, it } from "vitest";
import {
  MontarPalavraChute,
  PalavraJaFoiTentada,
  PrioridadeTeclado,
  TextoResultadoRanqueado,
} from "./jogo.js";

describe("jogo.js", () => {
  it("monta palavra do chute", () => {
    expect(MontarPalavraChute(["t", "e", "r", "m", "o"])).toBe("termo");
  });

  it("detecta palavra repetida", () => {
    const hist = [{ palavra: "termo", letras: ["T", "E", "R", "M", "O"] }];
    expect(PalavraJaFoiTentada("termo", hist)).toBe(true);
    expect(PalavraJaFoiTentada("terno", hist)).toBe(false);
  });

  it("prioridade do teclado", () => {
    expect(PrioridadeTeclado("correto", "presente")).toBe("correto");
    expect(PrioridadeTeclado("ausente", "presente")).toBe("presente");
  });

  it("texto de derrota ranqueada por abandono (1 mapa)", () => {
    const D = {
      metaVitorias: 2,
      placar: [
        { souEu: true, vitoriasRodada: 0, nomeJogador: "Eu" },
        { vitoriasRodada: 1, nomeJogador: "gabielite" },
      ],
    };
    const txt = TextoResultadoRanqueado(D, D.placar[1], false);
    expect(txt).toContain("0–1");
    expect(txt).toContain("gabielite");
    expect(txt).toMatch(/venceu o duelo/);
    expect(txt).not.toMatch(/1 mapas/);
  });

  it("texto de vitória na série (2 mapas)", () => {
    const D = {
      metaVitorias: 2,
      placar: [
        { souEu: true, vitoriasRodada: 2, nomeJogador: "Eu" },
        { vitoriasRodada: 0, nomeJogador: "Opp" },
      ],
    };
    const txt = TextoResultadoRanqueado(D, D.placar[0], true);
    expect(txt).toMatch(/2 mapas/);
    expect(txt).toMatch(/você venceu/);
  });
});
