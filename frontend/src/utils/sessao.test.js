import { describe, expect, it } from "vitest";
import { MontarPayloadSessao } from "./sessao.js";

describe("MontarPayloadSessao", () => {
  it("mantém arena na sessão quando encerrada só indica fim da rodada", () => {
    const payload = MontarPayloadSessao({
      modo: "arena",
      codigoSala: "ABC123",
      idJogador: "j1",
      encerrada: true,
      dadosSala: { partidaEncerrada: false, estadoSala: "entre_rodadas" },
      configArena: { maximoJogadores: 4 },
      view: "jogo",
    });
    expect(payload?.arena?.codigoSala).toBe("ABC123");
    expect(payload?.arena?.view).toBe("jogo");
  });

  it("persiste arena no lobby após sessão encerrada", () => {
    const payload = MontarPayloadSessao({
      modo: "arena",
      codigoSala: "ABC123",
      idJogador: "j1",
      idPartida: "uuid-arena",
      tokenSessao: "tok",
      encerrada: true,
      dadosSala: { partidaEncerrada: true, estadoSala: "encerrada" },
      view: "arenaLobby",
    });
    expect(payload?.arena?.codigoSala).toBe("ABC123");
    expect(payload?.arena?.view).toBe("arenaLobby");
    expect(payload?.arena?.partidaEncerrada).toBe(true);
  });

  it("persiste idPartida e tokenSessao na arena", () => {
    const payload = MontarPayloadSessao({
      modo: "arena",
      codigoSala: "GMVXGJ",
      idJogador: "j1",
      idPartida: "uuid-partida",
      tokenSessao: "token-secreto",
      dadosSala: { partidaEncerrada: false, estadoSala: "jogando" },
      configArena: {},
      view: "jogo",
    });
    expect(payload?.arena?.idPartida).toBe("uuid-partida");
    expect(payload?.arena?.tokenSessao).toBe("token-secreto");
    expect(payload?.arena?.codigoSala).toBe("GMVXGJ");
  });

  it("persiste credenciais na ranqueada", () => {
    const payload = MontarPayloadSessao({
      modo: "ranqueada",
      codigoSala: "DUEL01",
      idJogador: "j2",
      idPartida: "uuid-ranq",
      tokenSessao: "tok-ranq",
      dadosSala: { partidaEncerrada: false, estadoSala: "jogando" },
      view: "jogo",
    });
    expect(payload?.ranqueada?.idPartida).toBe("uuid-ranq");
    expect(payload?.ranqueada?.tokenSessao).toBe("tok-ranq");
  });
});
