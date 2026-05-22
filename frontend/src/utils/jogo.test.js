import { describe, expect, it } from "vitest";
import {
  MontarPalavraChute,
  PalavraJaFoiTentada,
  PrioridadeTeclado,
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
});
