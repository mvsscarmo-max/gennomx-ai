import { defineConfig, devices } from "@playwright/test";

const port = process.env.E2E_PORT ?? "3100";
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `node node_modules/next/dist/bin/next dev --port ${port}`,
    url: `${baseURL}/ai/companies`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      E2E_BYPASS_AUTH: "true",
      NEXT_PUBLIC_BASE_PATH: "/ai",
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000",
    },
  },
});
