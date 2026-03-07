import { test, expect } from "@playwright/test";
import { clearAppState, login } from "./helpers";

test.beforeEach(async ({ page }) => {
  await clearAppState(page);
});

test("login com credenciais válidas → redireciona para dashboard", async ({ page }) => {
  await page.fill('input[type="email"]', "consultor@empresa.com");
  await page.fill('input[type="password"]', "senha123");
  await page.click('button[type="submit"]');

  // Mock auth has 600 ms delay then redirects to /
  await page.waitForURL("/", { timeout: 5000 });
  await expect(page).toHaveURL("/");
});

test("login com campos vazios → exibe mensagem de erro", async ({ page }) => {
  // Submit without filling anything
  await page.click('button[type="submit"]');

  const errorMsg = page.locator("text=Preencha e-mail e senha");
  await expect(errorMsg).toBeVisible();

  // Should stay on /login
  await expect(page).toHaveURL("/login");
});

test("logout → redireciona para /login", async ({ page, isMobile }) => {
  test.skip(isMobile, "Logout button is in desktop sidebar only");

  await login(page);

  // Sidebar logout button (title="Sair")
  await page.click('button[title="Sair"]');

  await page.waitForURL("/login", { timeout: 3000 });
  await expect(page).toHaveURL("/login");
});

test("rota protegida sem auth → redireciona para /login", async ({ page }) => {
  // No login — navigate directly to a protected route
  await page.goto("/pipeline");
  await expect(page).toHaveURL("/login");
});

test("rota protegida /settings sem auth → redireciona para /login", async ({ page }) => {
  await page.goto("/settings");
  await expect(page).toHaveURL("/login");
});

test("mobile: login funciona em 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });

  await page.fill('input[type="email"]', "mobile@logia.com");
  await page.fill('input[type="password"]', "teste123");

  const submitBtn = page.locator('button[type="submit"]');
  await expect(submitBtn).toBeVisible();
  await submitBtn.click();

  await page.waitForURL("/", { timeout: 5000 });
  await expect(page).toHaveURL("/");
});
