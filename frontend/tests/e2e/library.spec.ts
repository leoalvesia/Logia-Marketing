import { test, expect } from "@playwright/test";
import { clearAppState, login, navigateTo } from "./helpers";

test.beforeEach(async ({ page }) => {
  await clearAppState(page);
  await login(page);
  await navigateTo(page, "/library");
  // Wait for the copy count to appear (Copys tab is default)
  await expect(page.locator("text=/\\d+ cop/")).toBeVisible({ timeout: 5000 });
});

test("filtrar copies por canal → lista atualiza corretamente", async ({ page }) => {
  const countLocator = page.locator("text=/\\d+ cop/");
  const allText = await countLocator.textContent();
  const allCount = parseInt(allText ?? "0");

  // Click Instagram channel filter (button wrapping a span[title="Instagram"])
  await page.locator('button:has(span[title="Instagram"])').click();

  // Count should differ from total
  await expect(countLocator).not.toHaveText(new RegExp(`^${allCount} cop`));

  // Clear filter
  await page.locator("text=× limpar").click();
  await expect(countLocator).toContainText(String(allCount));
});

test("filtrar por status rascunho → mostra apenas rascunhos", async ({ page }) => {
  const countLocator = page.locator("text=/\\d+ cop/");
  const allText = await countLocator.textContent();
  const allCount = parseInt(allText ?? "0");

  await page.locator("select").selectOption("draft");

  const filteredText = await countLocator.textContent();
  const filteredCount = parseInt(filteredText ?? "0");
  expect(filteredCount).toBeLessThan(allCount);
  expect(filteredCount).toBeGreaterThan(0);
});

test("clicar 'Gerar Arte' em copy → botão acessível no hover", async ({ page }) => {
  // Hover the first copy card to reveal action buttons
  const firstCard = page.locator(".space-y-2 > div").first();
  await firstCard.hover();

  // "Gerar Arte" appears on CSS group-hover
  const gerarArteBtn = page.locator("button:has-text('Gerar Arte')").first();
  await expect(gerarArteBtn).toBeVisible({ timeout: 2000 });
  await expect(gerarArteBtn).toBeEnabled();
});

test("paginação: navegar para página 2 → carrega próximos itens", async ({ page }) => {
  // 42 copies ÷ 20 per page → page buttons 1, 2, 3 visible
  const page2Btn = page.locator("button", { hasText: "2" }).first();
  await expect(page2Btn).toBeVisible();

  await page2Btn.click();

  // Copy cards still visible after pagination
  await expect(page.locator(".space-y-2 > div").first()).toBeVisible();

  // Can go back to page 1
  const page1Btn = page.locator("button", { hasText: "1" }).first();
  await page1Btn.click();
  await expect(page.locator(".space-y-2 > div").first()).toBeVisible();
});

test("navegar para aba Arte → grade de artes visível", async ({ page }) => {
  await page.getByRole("tab", { name: "Arte" }).click();

  await expect(page.locator("text=/\\d+ artes/")).toBeVisible({ timeout: 3000 });
  await expect(page.locator(".grid .group").first()).toBeVisible();
});

test("download de arte → botão visível no hover", async ({ page }) => {
  await page.getByRole("tab", { name: "Arte" }).click();
  await expect(page.locator(".grid .group").first()).toBeVisible({ timeout: 3000 });

  // Hover first art card to reveal overlay
  const firstArt = page.locator(".grid .group").first();
  await firstArt.hover();

  const downloadBtn = page.locator('button[title="Download"]').first();
  await expect(downloadBtn).toBeVisible({ timeout: 2000 });
  await expect(downloadBtn).toBeEnabled();
});
