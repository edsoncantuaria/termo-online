import { test, expect } from "@playwright/test";

async function iniciarModo(page, nomeBotao) {
  await page.goto("/");
  await page.getByRole("button", { name: "Jogar" }).click();
  await page.getByRole("button", { name: nomeBotao }).click();
  await page.waitForTimeout(500);
  const aviso = page.getByRole("dialog").filter({ hasText: /Dueto|Quarteto/i });
  if (await aviso.isVisible().catch(() => false)) {
    await page.getByRole("button", { name: /Entendi/i }).click();
  }
  await expect(page.locator(".modo-jogo-multi")).toBeVisible({ timeout: 20000 });
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
  const grades = page.locator(".grade-multi");
  await expect(grades).toHaveCount(2, { timeout: 15000 });

  await digitarChute(page, "termo");
  const linhasPreenchidas = page.locator(".grade-multi .grade-linha .peca.preenchida");
  await expect(linhasPreenchidas.first()).toBeVisible({ timeout: 10000 });
});

test("quarteto: quatro grades", async ({ page }) => {
  await iniciarModo(page, /Quarteto/i);
  const grades = page.locator(".grade-multi");
  await expect(grades).toHaveCount(4, { timeout: 15000 });

  await digitarChute(page, "termo");
  const pecas = page.locator(".grade-multi .peca.correto, .grade-multi .peca.presente, .grade-multi .peca.ausente");
  await expect(pecas.first()).toBeVisible({ timeout: 10000 });
});
