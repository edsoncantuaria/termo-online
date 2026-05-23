import { test, expect } from "@playwright/test";
import { abrirAjuda, dispensarTutorial } from "./helpers/sala-arena.js";

test("home carrega título e salas públicas", async ({ page }) => {
  await page.goto("/");
  await dispensarTutorial(page);
  await expect(page.getByRole("heading", { name: /Descubra a palavra/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Salas públicas" })).toBeVisible();
});

test("ajuda abre e mostra sons", async ({ page }) => {
  await page.goto("/");
  await dispensarTutorial(page);
  await abrirAjuda(page, "Ajustes");
  await expect(page.getByText("Sons", { exact: true })).toBeVisible();
});

test("ajuda menciona nível e XP", async ({ page }) => {
  await page.goto("/");
  await dispensarTutorial(page);
  await abrirAjuda(page, "Modos");
  await expect(page.getByText(/2200 XP\/dia/i)).toBeVisible();
});
