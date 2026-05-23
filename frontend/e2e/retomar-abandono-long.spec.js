import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect } from "@playwright/test";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

test.describe.configure({ timeout: 120_000 });

test("abandono prolongado: retomar somenteResultado (pytest integração)", () => {
  const saida = execSync(
    ".venv/bin/python3 -m pytest tests/test_api_retomar_abandono_long.py tests/test_partida_sessao.py::test_retomar_apos_abandono_prolongado_somente_resultado tests/test_partida_sessao.py::test_processar_salas_offline_apos_restart_simulado -q",
    { cwd: RAIZ, encoding: "utf8" }
  );
  expect(saida).toContain("passed");
});

test("tempo do servidor exposto na API", async ({ request }) => {
  const R = await request.get("/api/tempo");
  expect(R.ok()).toBeTruthy();
  const D = await R.json();
  expect(D.dataDiaBrasil).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  expect(D.segundosAteMeiaNoiteBrasil).toBeGreaterThan(0);
});
