import { test, expect } from "@playwright/test";

test("prática: chute repetido é rejeitado", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Jogar" }).click();
  await page.getByRole("button", { name: /Prática/i }).click();
  await page.waitForURL(/view=jogo|\/\?/, { timeout: 15000 }).catch(() => {});

  const grid = page.locator(".grade-linha").first();
  await expect(grid).toBeVisible({ timeout: 20000 });

  async function digitarPalavra(palavra) {
    for (const L of palavra) {
      await page.keyboard.press(L);
    }
    await page.keyboard.press("Enter");
  }

  await digitarPalavra("termo");
  await page.waitForTimeout(800);
  await digitarPalavra("termo");
  await expect(page.locator(".toast.erro")).toContainText(/já tentou/i, {
    timeout: 8000,
  });
});

test("health da API", async ({ request }) => {
  const R = await request.get("/api/health");
  expect(R.ok()).toBeTruthy();
  const J = await R.json();
  expect(J.status).toBe("ok");
});
