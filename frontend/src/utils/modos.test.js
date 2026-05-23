import { describe, expect, it } from "vitest";
import { PartidaRanqueadaAtiva } from "./modos.js";

describe("PartidaRanqueadaAtiva", () => {
  it("detecta duelo ranqueado ativo fora da view jogo", () => {
    expect(
      PartidaRanqueadaAtiva({
        modo: "ranqueada",
        idPartida: "p1",
        idJogador: "j1",
        espectador: false,
        dadosSala: { partidaEncerrada: false },
        view: "inicio",
      })
    ).toBe(true);
  });

  it("ignora partida encerrada ou espectador", () => {
    expect(
      PartidaRanqueadaAtiva({
        modo: "ranqueada",
        idPartida: "p1",
        idJogador: "j1",
        espectador: true,
        dadosSala: {},
      })
    ).toBe(false);
    expect(
      PartidaRanqueadaAtiva({
        modo: "ranqueada",
        idPartida: "p1",
        idJogador: "j1",
        espectador: false,
        dadosSala: { partidaEncerrada: true },
      })
    ).toBe(false);
  });
});
