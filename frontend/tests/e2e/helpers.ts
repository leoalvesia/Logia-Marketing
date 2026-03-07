import { Page } from "@playwright/test";

/**
 * Navigate to /login and wipe all persisted Zustand stores.
 * Must be called before login() — it lands on the /login form.
 */
export async function clearAppState(page: Page) {
  await page.goto("/login");
  await page.evaluate(() => {
    localStorage.removeItem("logia-auth");
    localStorage.removeItem("logia-settings-v2");
    sessionStorage.clear();
  });
}

/**
 * Fill and submit the login form.
 * Assumes the page is already at /login (call clearAppState first).
 * Mock auth accepts any non-empty credentials with a 600 ms delay.
 */
export async function login(
  page: Page,
  email = "test@logia.com",
  password = "senha123"
) {
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL("/", { timeout: 5000 });
}

/**
 * Navigate to a protected route via SPA link click (preserves in-memory
 * Zustand state, avoiding the async-rehydration race on full page.goto).
 */
export async function navigateTo(page: Page, path: string) {
  // :visible filters out the hidden sidebar on mobile (md:hidden) and the
  // hidden BottomNav on desktop (md:hidden → display:none), ensuring exactly
  // one matching link regardless of viewport.
  await page.locator(`a:visible[href="${path}"]`).click();
  await page.waitForURL(path, { timeout: 5000 });
}
