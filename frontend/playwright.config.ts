import { defineConfig } from "@playwright/test";

export default defineConfig({
  globalTeardown: "./e2e/teardown.ts",
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:5173",
    viewport: { width: 1440, height: 1000 },
  },
  webServer: [
    {
      command: `${process.env.PYTHON || "python"} ../scripts/run_e2e_api.py`,
      url: "http://127.0.0.1:9001/health",
      timeout: 60000,
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      env: { API_PROXY_TARGET: "http://127.0.0.1:9001" },
      timeout: 60000,
    },
  ],
});
