import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for AutoFlow E2E tests.
 *
 * NOTE: these tests were written but could NOT be executed in the
 * environment that generated this repository, because that sandbox's
 * network egress allowlist blocks cdn.playwright.dev (the host Playwright
 * downloads browser binaries from). See docs/ai-testing-log.md and
 * evidence/testing/test-summary.md for details. Run
 * `npx playwright install chromium` once on a machine with normal
 * internet access, then `npx playwright test` from frontend/.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    
   {
    command:'cd ../backend && if exist e2e_test.db del /f e2e_test.db && set "DATABASE_URL=sqlite:///./e2e_test.db" && venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
    url: "http://127.0.0.1:8000/health",
    reuseExistingServer: false,
    timeout: 30_000,
   },
    {
      command: "npm run dev -- --port 5173 --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
