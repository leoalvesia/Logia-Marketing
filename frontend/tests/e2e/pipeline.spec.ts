import { test, expect } from "@playwright/test";
import { clearAppState, login, navigateTo } from "./helpers";

// Pipeline mock timings:
//  RESEARCHING   → 2 500 ms → ORCHESTRATING
//  ORCHESTRATING → 2 000 ms → AWAITING_SELECTION
//  Topic select  → 3 000 ms → COPY_REVIEW
//  Approve copy  → 2 500 ms → ART_REVIEW

test.beforeEach(async ({ page }) => {
  await clearAppState(page);
  await login(page);
  await navigateTo(page, "/pipeline");
  await expect(page.locator("text=Iniciar Novo Post")).toBeVisible({ timeout: 5000 });
});

test("iniciar pipeline → selecionar canais → confirma pesquisa iniciada", async ({ page }) => {
  await page.click("text=Iniciar Novo Post");
  await expect(page.locator("text=Selecione os canais")).toBeVisible();

  // Select Instagram channel card
  await page.locator("button:has-text('Instagram')").first().click();
  await expect(page.locator("text=1 canal selecionado")).toBeVisible();

  await page.click("button:has-text('Iniciar Pesquisa')");

  // Research loading screen appears
  await expect(
    page.locator("text=Coletando e analisando fontes")
  ).toBeVisible({ timeout: 5000 });
});

test("selecionar tema da lista → avança para copy", async ({ page }) => {
  await page.click("text=Iniciar Novo Post");
  await page.locator("button:has-text('LinkedIn')").first().click();
  await page.click("button:has-text('Iniciar Pesquisa')");

  // Wait for topic list (RESEARCHING 2.5s + ORCHESTRATING 2s)
  await expect(page.locator("text=Escolha um tema")).toBeVisible({ timeout: 12000 });

  // Click first topic CTA
  await page.locator("button:has-text('Usar este tema')").first().click();

  // Should show generating copy or copy editor
  await expect(
    page.locator("text=Aprovar Todas").or(page.locator("text=Gerando copies"))
  ).toBeVisible({ timeout: 8000 });
});

test("editar copy → aprovar → avança para arte", async ({ page }) => {
  await page.click("text=Iniciar Novo Post");
  await page.locator("button:has-text('Instagram')").first().click();
  await page.click("button:has-text('Iniciar Pesquisa')");

  await expect(page.locator("text=Escolha um tema")).toBeVisible({ timeout: 12000 });
  await page.locator("button:has-text('Usar este tema')").first().click();

  // Wait for copy editor
  const approveBtn = page.locator("button:has-text('Aprovar Todas')");
  await expect(approveBtn).toBeVisible({ timeout: 8000 });

  // Edit the first textarea if visible
  const firstTextarea = page.locator("textarea").first();
  if (await firstTextarea.isVisible()) {
    await firstTextarea.click();
    await firstTextarea.selectText();
    await firstTextarea.type("Copy editada manualmente pelo teste E2E.");
  }

  await approveBtn.click();

  // Should advance to art generation
  await expect(
    page.locator("text=Agente de arte criando variações visuais")
  ).toBeVisible({ timeout: 8000 });
});

test("WebSocket: status atualiza sem refresh de página", async ({ page }) => {
  await page.click("text=Iniciar Novo Post");
  await page.locator("button:has-text('Twitter')").first().click();
  await page.click("button:has-text('Iniciar Pesquisa')");

  // Step 1: RESEARCHING (no page reload — same SPA context)
  await expect(
    page.locator("text=Coletando e analisando fontes")
  ).toBeVisible({ timeout: 5000 });
  await expect(page).toHaveURL("/pipeline");

  // Step 2: transitions to ORCHESTRATING in place
  await expect(
    page.locator("text=Orquestrando agentes e priorizando temas")
  ).toBeVisible({ timeout: 5000 });
  await expect(page).toHaveURL("/pipeline");

  // Step 3: AWAITING_SELECTION — still /pipeline, no refresh
  await expect(page.locator("text=Escolha um tema")).toBeVisible({ timeout: 8000 });
  await expect(page).toHaveURL("/pipeline");
});

test("mobile: pipeline navegável em tela pequena", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });

  // Idle CTA visible on mobile
  await expect(page.locator("text=Iniciar Novo Post")).toBeVisible();
  await page.click("text=Iniciar Novo Post");

  // Channel selector visible at 390px
  await expect(page.locator("text=Selecione os canais")).toBeVisible();

  // Select channel and start
  await page.locator("button:has-text('Instagram')").first().click();
  await page.click("button:has-text('Iniciar Pesquisa')");

  await expect(
    page.locator("text=Coletando e analisando fontes")
  ).toBeVisible({ timeout: 5000 });
});
