import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
  },
  webServer: process.env.CI
    ? [
        {
          command:
            "cd .. && PYTHONPATH=src ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000",
          url: "http://127.0.0.1:8000/api/ranqueada/elos",
          reuseExistingServer: false,
          timeout: 120000,
        },
        {
          command: "npm run dev -- --host 127.0.0.1 --port 5173",
          url: "http://127.0.0.1:5173",
          reuseExistingServer: false,
          timeout: 120000,
        },
      ]
    : {
        command: "npm run dev -- --host 127.0.0.1 --port 5173",
        url: "http://127.0.0.1:5173",
        reuseExistingServer: true,
        timeout: 120000,
      },
});
