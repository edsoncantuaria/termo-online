import { test, expect } from "@playwright/test";

test("solo: palavra inválida é rejeitada pela API (não só no cliente)", async ({
  request,
}) => {
  const ini = await request.post("/api/jogar/iniciar", {
    data: { nomeJogador: "e2e-val", modo: "dueto" },
  });
  expect(ini.ok()).toBeTruthy();
  const { idPartida, tokenPartida } = await ini.json();
  const chute = await request.post("/api/jogar/chute", {
    data: {
      idPartida,
      tokenPartida,
      palavra: "xxxxx",
      nomeJogador: "e2e-val",
    },
  });
  expect(chute.ok()).toBeTruthy();
  const corpo = await chute.json();
  expect(corpo.valido).toBe(false);
  expect(corpo.mensagem).toMatch(/dicionário/i);
});

test("prática: iniciar partida na API continua rejeitado", async ({ request }) => {
  const R = await request.post("/api/jogar/iniciar", {
    data: { nomeJogador: "e2e", modo: "pratica" },
  });
  expect(R.status()).toBe(410);
});
