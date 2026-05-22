import { test, expect } from "@playwright/test";

test("home carrega título e salas públicas", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Descubra a palavra/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Salas públicas" })).toBeVisible();
});

test("ajuda abre e mostra sons", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Ajuda" }).click();
  await expect(page.getByText("Sons do jogo")).toBeVisible();
});

test("ajuda menciona nível e XP", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Ajuda" }).click();
  await page.getByRole("button", { name: "Modos" }).click();
  await expect(page.getByText(/2200 XP\/dia/i)).toBeVisible();
});
