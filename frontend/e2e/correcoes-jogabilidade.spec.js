import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect } from "@playwright/test";
import {
  digitarPalavra,
  prepararArenaDoisJogadores,
  metaArena,
  tentativasUsadasApi,
  chuteInvalidoViaWs,
} from "./helpers/sala-arena.js";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

test.describe.configure({ timeout: 90_000 });

test.describe("Correções de jogabilidade", () => {
  test("1. bot: filtro respeita letras verdes (pytest)", () => {
    const saida = execSync(
      ".venv/bin/python3 -m pytest tests/test_bot_jogador.py -q",
      { cwd: RAIZ, encoding: "utf8" }
    );
    expect(saida).toContain("passed");
  });

  test("4/D. dueto e quarteto: máximo de tentativas na API", async ({
    request,
  }) => {
    const dueto = await request.post("/api/jogar/iniciar", {
      data: { nomeJogador: "e2e-dueto", modo: "dueto" },
    });
    expect(dueto.ok()).toBeTruthy();
    expect((await dueto.json()).maximoTentativas).toBe(7);

    const quarteto = await request.post("/api/jogar/iniciar", {
      data: { nomeJogador: "e2e-quarteto", modo: "quarteto" },
    });
    expect(quarteto.ok()).toBeTruthy();
    expect((await quarteto.json()).maximoTentativas).toBe(9);
  });

  test("4/D. pontuação dueto na 6ª tentativa (pytest)", () => {
    const saida = execSync(
      ".venv/bin/python3 -m pytest tests/test_pontuacao_modos.py -q",
      { cwd: RAIZ, encoding: "utf8" }
    );
    expect(saida).toContain("passed");
  });

  test("6/B. arena: chute inválido não grava tentativa (pytest)", () => {
    const saida = execSync(
      ".venv/bin/python3 -m pytest tests/test_chute_arena.py -q",
      { cwd: RAIZ, encoding: "utf8" }
    );
    expect(saida).toContain("passed");
  });

  test("6/B. arena: WebSocket devolve chuteInvalido sem incrementar tentativas", async ({
    browser,
    request,
  }) => {
    const { host, codigo } = await prepararArenaDoisJogadores(
      browser,
      request,
      "E2EWsHost",
      "E2EWsGuest"
    );
    const meta = await metaArena(host);
    const antes = await tentativasUsadasApi(
      request,
      codigo,
      meta.idJogador
    );

    const resposta = await chuteInvalidoViaWs(host, "xxxxx");
    expect(resposta.tipo).toBe("chuteInvalido");
    expect(resposta.mensagem).toMatch(/dicionário/i);

    const depois = await tentativasUsadasApi(
      request,
      codigo,
      meta.idJogador
    );
    expect(depois).toBe(antes);
  });

  test("2/B. arena: palavra inválida permanece na grade", async ({
    browser,
    request,
  }) => {
    const { host } = await prepararArenaDoisJogadores(
      browser,
      request,
      "E2EInvHost",
      "E2EInvGuest"
    );

    await digitarPalavra(host, "xxxxx");
    await expect(host.locator(".toast.erro")).toContainText(/dicionário/i, {
      timeout: 8000,
    });

    const celulas = host.locator(".grade .linha .tile.preenchida");
    await expect(celulas).toHaveCount(5);
    await expect(celulas.nth(0)).toHaveText(/x/i);
    await expect(celulas.nth(4)).toHaveText(/x/i);
  });

  test("3/C. arena: Enter duplo não envia duas tentativas", async ({
    browser,
    request,
  }) => {
    const { host, codigo } = await prepararArenaDoisJogadores(
      browser,
      request,
      "E2EDblHost",
      "E2EDblGuest"
    );
    const meta = await metaArena(host);

    await digitarPalavra(host, "xxxxx", { enviar: false });
    await host.keyboard.press("Enter");
    await host.keyboard.press("Enter");

    await expect(host.locator(".toast.erro")).toContainText(/dicionário/i, {
      timeout: 8000,
    });
    await host.waitForTimeout(1200);

    const usadas = await tentativasUsadasApi(
      request,
      codigo,
      meta.idJogador
    );
    expect(usadas).toBe(0);
    await expect(host.locator(".tentativas-dots .dot.usada")).toHaveCount(0);
  });

  test("5/E. prática: roda no dispositivo com dicionário em cache", async ({
    page,
    request,
  }) => {
    const Info = await request.get("/api/dicionario/info");
    expect(Info.ok()).toBeTruthy();
    const { hash } = await Info.json();
    const Palavras = await request.get("/api/dicionario/palavras");
    expect(Palavras.ok()).toBeTruthy();
    const { palavras } = await Palavras.json();

    await page.goto("/");
    await dispensarTutorial(page);
    await page.evaluate(
      ([h, lista]) => {
        localStorage.setItem("termoDicionarioHash", h);
        localStorage.setItem("termoDicionarioPalavras", JSON.stringify(lista));
      },
      [hash, palavras.slice(0, 500)]
    );

    await page.getByRole("button", { name: /Jogar/i }).click();
    await page.getByRole("button", { name: /^Prática$/i }).click();
    await expect(page.locator(".grade")).toBeVisible({ timeout: 15000 });

    let bloqueouIniciar = false;
    page.on("request", (req) => {
      if (req.url().includes("/api/jogar/iniciar") && req.method() === "POST") {
        bloqueouIniciar = true;
      }
    });
    await page.waitForTimeout(500);
    expect(bloqueouIniciar).toBe(false);
  });
});
