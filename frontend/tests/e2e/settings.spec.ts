import { test, expect } from "@playwright/test";
import { clearAppState, login, navigateTo } from "./helpers";

test.beforeEach(async ({ page }) => {
  await clearAppState(page);
  await login(page);
  await navigateTo(page, "/settings");
  // Use the unique page heading (multiple elements contain "Configurações" text)
  await expect(page.locator("h1#settings-heading")).toBeVisible({ timeout: 5000 });
});

test("adicionar perfil monitorado → aparece na lista", async ({ page }) => {
  await page.getByRole("tab", { name: "Perfis Monitorados" }).click();
  await expect(page.locator('input[placeholder="@handle ou URL"]')).toBeVisible();

  const profilesBefore = await page.locator('[role="listitem"]').count();

  // @handle format required for instagram (default platform)
  await page.fill('input[placeholder="@handle ou URL"]', "@consultordigital");
  await page.click('button[aria-label="Adicionar perfil monitorado"]');

  // .first() avoids strict-mode error: toast title + ARIA live region both contain this text
  await expect(page.locator("text=Perfil adicionado").first()).toBeVisible({ timeout: 3000 });
  // Check the profile row specifically (p.font-mono = handle display in ProfileRow)
  await expect(page.locator("p.font-mono", { hasText: "@consultordigital" })).toBeVisible();

  const profilesAfter = await page.locator('[role="listitem"]').count();
  expect(profilesAfter).toBe(profilesBefore + 1);
});

test("toggle ativo/inativo → persiste ao recarregar", async ({ page }) => {
  await page.getByRole("tab", { name: "Perfis Monitorados" }).click();

  const firstRow = page.locator('[role="listitem"]').first();
  const toggle = firstRow.locator('button[aria-pressed]');
  await expect(toggle).toBeVisible({ timeout: 3000 });

  const stateBefore = await toggle.getAttribute("aria-pressed");
  await toggle.click();

  const stateAfterClick = await toggle.getAttribute("aria-pressed");
  expect(stateAfterClick).not.toBe(stateBefore);

  // Verify Zustand persisted the change to localStorage
  const savedActive = await page.evaluate(() => {
    const raw = localStorage.getItem("logia-settings-v2");
    if (!raw) return null;
    return JSON.parse(raw).state?.monitoredProfiles?.[0]?.active;
  });
  expect(savedActive).toBe(stateAfterClick === "true");

  // Verify state survives SPA navigation away and back (no full reload needed)
  await page.locator("a:visible[href='/']").click();
  await page.waitForURL("/");
  await navigateTo(page, "/settings");
  await page.getByRole("tab", { name: "Perfis Monitorados" }).click();

  const toggleAfterNav = page.locator('[role="listitem"]').first().locator('button[aria-pressed]');
  await expect(toggleAfterNav).toBeVisible({ timeout: 3000 });
  expect(await toggleAfterNav.getAttribute("aria-pressed")).toBe(stateAfterClick);
});

test("salvar nicho → confirmação de sucesso", async ({ page }) => {
  await page.getByRole("tab", { name: "Nicho" }).click();
  await expect(page.locator("#nicho-textarea")).toBeVisible();

  await page.fill("#nicho-textarea", "Consultor de marketing digital para PMEs brasileiras");
  await page.click('button[aria-label="Salvar configurações de nicho e persona"]');

  // .first() avoids strict-mode: toast div + ARIA status span both contain this text
  await expect(page.locator("text=Salvo com sucesso").first()).toBeVisible({ timeout: 3000 });
});

test("remover perfil monitorado → desaparece da lista", async ({ page }) => {
  await page.getByRole("tab", { name: "Perfis Monitorados" }).click();

  const profilesBefore = await page.locator('[role="listitem"]').count();
  expect(profilesBefore).toBeGreaterThan(0);

  const firstHandle = await page
    .locator('[role="listitem"]').first()
    .locator("p.font-mono").textContent();

  await page
    .locator('[role="listitem"]').first()
    .locator('button[aria-label^="Remover"]')
    .click();

  const profilesAfter = await page.locator('[role="listitem"]').count();
  expect(profilesAfter).toBe(profilesBefore - 1);

  if (firstHandle) {
    await expect(page.locator(`text=${firstHandle}`)).not.toBeVisible();
  }
});

test("adicionar perfil com handle vazio → exibe erro de validação", async ({ page }) => {
  await page.getByRole("tab", { name: "Perfis Monitorados" }).click();
  await page.click('button[aria-label="Adicionar perfil monitorado"]');
  await expect(page.locator('[role="alert"]')).toContainText("Campo obrigatório", { timeout: 2000 });
});
