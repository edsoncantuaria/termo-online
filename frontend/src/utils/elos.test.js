import { describe, expect, it } from "vitest";
import { CaiuDeElo, SubiuDeElo } from "./elos.js";

describe("elos.js", () => {
  it("detecta subida de elo", () => {
    expect(SubiuDeElo("bronze", "prata")).toBe(true);
    expect(SubiuDeElo("prata", "prata")).toBe(false);
    expect(SubiuDeElo("ouro", "bronze")).toBe(false);
  });

  it("detecta queda de elo", () => {
    expect(CaiuDeElo("prata", "bronze")).toBe(true);
    expect(CaiuDeElo("bronze", "bronze")).toBe(false);
    expect(CaiuDeElo("bronze", "prata")).toBe(false);
  });
});
