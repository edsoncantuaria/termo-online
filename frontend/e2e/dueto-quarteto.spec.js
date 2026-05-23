import { test, expect } from "@playwright/test";
import {
  dispensarTutorial,
  escolherModoJogar,
  garantirNickVisitante,
} from "./helpers/sala-arena.js";

async function iniciarModo(page, nomeBotao) {
  const nick = `e2e${Date.now().toString(36).slice(-5)}`;
  await page.goto("/");
  await dispensarTutorial(page);
  await page
    .getByRole("banner")
    .getByRole("button", { name: "Entrar" })
    .click({ force: true });
  await expect(page.locator("dialog.dialog-conta")).toBeVisible({
    timeout: 10_000,
  });
  await garantirNickVisitante(page, nick);
  await escolherModoJogar(page, nomeBotao);
  const aviso = page.getByRole("dialog").filter({ hasText: /Dueto|Quarteto/i });
  if (await aviso.isVisible().catch(() => false)) {
    await page.getByRole("button", { name: /Entendi/i }).click({ force: true });
  }
  await expect(page.locator(".grades-multi")).toBeVisible({ timeout: 25_000 });
}

async function digitarChute(page, palavra) {
  for (const L of palavra) {
    await page.keyboard.press(L);
  }
  await page.keyboard.press("Enter");
  await page.waitForTimeout(900);
}

test("dueto: duas grades e chute válido", async ({ page }) => {
  await iniciarModo(page, /Dueto/i);
  const grades = page.locator(".grade-multi-item");
  await expect(grades).toHaveCount(2, { timeout: 15_000 });

  await digitarChute(page, "termo");
  const linhasPreenchidas = page.locator(
    ".grades-multi .tile.preenchida, .grades-multi .peca.preenchida"
  );
  await expect(linhasPreenchidas.first()).toBeVisible({ timeout: 10000 });
});

test("quarteto: quatro grades", async ({ page }) => {
  await iniciarModo(page, /Quarteto/i);
  const grades = page.locator(".grade-multi-item");
  await expect(grades).toHaveCount(4, { timeout: 15_000 });

  await digitarChute(page, "termo");
  const pecas = page.locator(
    ".grades-multi .tile.correto, .grades-multi .tile.presente, .grades-multi .tile.ausente, .grades-multi .peca.correto, .grades-multi .peca.presente, .grades-multi .peca.ausente"
  );
  await expect(pecas.first()).toBeVisible({ timeout: 10000 });
});
