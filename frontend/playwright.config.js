import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DADOS_E2E = path.join(RAIZ, "data", "e2e");

const isolado = Boolean(process.env.CI);
const PYTHON = path.join(RAIZ, ".venv/bin/python");

const comandoApi =
  `cd "${RAIZ}" && mkdir -p "${DADOS_E2E}" && rm -f "${DADOS_E2E}/termo.db" && ` +
  `TERM0_DATA="${DADOS_E2E}" PYTHONPATH=src "${PYTHON}" -c ` +
  `"from nucleo import persistencia; persistencia.InicializarBanco()" && ` +
  `TERM0_DATA="${DADOS_E2E}" PYTHONPATH=src "${PYTHON}" -m uvicorn main:Aplicacao --host 127.0.0.1 --port 8000`;

export default defineConfig({
  testDir: "e2e",
  workers: isolado ? 1 : undefined,
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    reducedMotion: "reduce",
  },
  webServer: isolado
    ? [
        {
          command: comandoApi,
          url: "http://127.0.0.1:8000/api/health",
          reuseExistingServer: false,
          timeout: 120_000,
        },
        {
          command: "npm run dev -- --host 127.0.0.1 --port 5173",
          url: "http://127.0.0.1:5173",
          reuseExistingServer: false,
          timeout: 120_000,
        },
      ]
    : {
        command: "npm run dev -- --host 127.0.0.1 --port 5173",
        url: "http://127.0.0.1:5173",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
