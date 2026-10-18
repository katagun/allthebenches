import { test, expect, type Page } from '@playwright/test';

async function ready(page: Page) {
  await page.goto('./');
  await expect(page.locator('tbody tr').first()).toBeVisible();
  await expect(page.getByText('Updating comparison…', { exact: false })).toHaveCount(0);
}

async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
}

for (const width of [320, 375, 390, 430, 768, 1024]) {
  for (const orientation of ['benchmarks', 'models']) {
    test(`${width}px ${orientation}: space budget, controls and sticky scrolling`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      await ready(page);
      if (orientation === 'models') {
        await page.getByRole('button', { name: 'Options', exact: true }).click();
        await page.getByRole('combobox', { name: 'Table orientation' }).click();
        await page.getByRole('option', { name: 'Model rows', exact: true }).click();
        await page.getByRole('button', { name: 'Options', exact: true }).click();
      }
      await noOverflow(page);
      const card = await page.locator('.table-card').boundingBox();
      expect(card!.y).toBeLessThan(320);
      expect(card!.height).toBeGreaterThan(844 * 0.5);
      const header = await page.locator('thead').boundingBox();
      expect(header!.height).toBeLessThan(190);
      await expect(page.getByRole('button', { name: 'Options', exact: true })).toHaveAttribute('aria-expanded', 'false');
      // All-model coverage provides enough rows to require vertical scrolling.
      await page.getByRole('button', { name: 'All models', exact: true }).click();
      await expect(page.locator('tbody tr').nth(15)).toBeAttached();
      const scroll = page.locator('[data-slot="table-container"]');
      await scroll.evaluate(el => { el.scrollTop = 350; el.scrollLeft = 150; });
      await expect.poll(() => scroll.evaluate(el => el.scrollTop)).toBeGreaterThan(100);
      const positions = await scroll.evaluate(el => {
        const box = el.getBoundingClientRect();
        const head = el.querySelector('thead th')!.getBoundingClientRect();
        const label = el.querySelector('tbody .sticky-model-cell')!.getBoundingClientRect();
        return { top: head.top - box.top, left: label.left - box.left, horizontal: el.scrollLeft, overflow: el.scrollWidth - el.clientWidth };
      });
      expect(Math.abs(positions.top)).toBeLessThanOrEqual(2);
      expect(Math.abs(positions.left)).toBeLessThanOrEqual(2);
      if (positions.overflow > 1) expect(positions.horizontal).toBeGreaterThan(0);
      await noOverflow(page);
      await page.getByRole('button', { name: 'Options', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Filters', exact: true })).toBeVisible();
      await noOverflow(page);
      await page.getByRole('button', { name: 'Filters', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Apply filters', exact: true })).toBeInViewport();
      await noOverflow(page);
      await page.getByRole('button', { name: 'Cancel', exact: true }).click();
    });
  }
}

test('desktop toolbar stays on one row', async ({ page }) => {
  await page.setViewportSize({ width: 1422, height: 900 });
  await ready(page);
  await expect(page.getByRole('button', { name: 'Options', exact: true })).toBeHidden();
  await noOverflow(page);
  const centers = await page.locator('.primary-controls .toolbar > :not(.dense-toggle)').evaluateAll(elements => elements.map(el => {
    const r = el.getBoundingClientRect(); return r.top + r.height / 2;
  }));
  expect(Math.max(...centers) - Math.min(...centers)).toBeLessThan(3);
});

for (const width of [375, 390, 430]) {
  test(`${width}px optional dense matrix fits four or five models`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await ready(page);
    await page.getByRole('button', { name: 'Options', exact: true }).click();
    await page.getByRole('button', { name: 'Dense matrix', exact: true }).click();
    await page.getByRole('button', { name: 'Options', exact: true }).click();
    await expect(page.locator('thead th')).toHaveCount(width === 430 ? 6 : 5);
    const scroll = page.locator('[data-slot="table-container"]');
    expect(await scroll.evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(1);
    await noOverflow(page);
  });
}

for (const width of [390, 1422]) {
  test(`${width}px choose models, compare and restore shared state`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await ready(page);
    await page.getByRole('button', { name: 'Choose models', exact: true }).click();
    await page.getByRole('searchbox', { name: 'Find a model' }).fill('Claude 3');
    const choices = page.getByRole('dialog').getByRole('checkbox');
    await choices.nth(0).check();
    await choices.nth(1).check();
    await page.getByRole('button', { name: 'Compare selected models', exact: true }).click();
    await expect(page.locator('thead th')).toHaveCount(3);
    await expect(page.locator('.selection-strip button')).toHaveCount(2);
    await noOverflow(page);
    await page.reload();
    await expect(page.locator('thead th')).toHaveCount(3);
    await expect(page.getByRole('button', { name: 'Compare', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await page.getByRole('button', { name: 'Explore', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Explore', exact: true })).toHaveAttribute('aria-pressed', 'true');
  });
}

test('picker permits more than five selections and discards cancelled edits', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  await page.getByRole('button', { name: 'Compare', exact: true }).click();
  const choices = page.getByRole('dialog').getByRole('checkbox');
  for (let i = 0; i < 8; i++) await choices.nth(i).check();
  await expect(choices.nth(7)).toBeChecked();
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await expect(page.locator('.selection-strip')).toHaveCount(0);
  await page.getByRole('button', { name: 'Compare', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Compare selected models', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await page.getByRole('button', { name: /^Options/ }).click();
  await page.getByRole('button', { name: 'Choose benchmarks', exact: true }).click();
  await page.getByRole('searchbox', { name: 'Find a benchmark' }).fill('GraphWalks');
  await expect(page.locator('.column-group').first()).toContainText('GraphWalks');
  await noOverflow(page);
});

for (const width of [390, 768, 1422]) {
  test(`${width}px model and benchmark pages, evidence and matrix return`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await ready(page);
    await page.getByRole('button', { name: 'All models', exact: true }).click();
    const matrixUrl = page.url();
    const modelName = await page.locator('.model-link').first().innerText();
    await page.locator('.model-link').first().click();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(modelName.trim());
    await expect(page.locator('.entity-score').first()).toBeVisible();
    await noOverflow(page);
    await page.reload();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(modelName.trim());
    await page.locator('.entity-score summary').first().click();
    await expect(page.locator('.entity-score details[open]')).toContainText('Source locator');
    await expect(page.locator('.entity-source-link').first()).toHaveAttribute('href', /^https?:/);
    await page.locator('.entity-score-title a').first().click();
    await expect(page.locator('.entity-kind')).toHaveText('Benchmark variant');
    await expect(page.locator('.entity-score').first()).toBeVisible();
    await noOverflow(page);
    await page.getByRole('searchbox', { name: 'Search scores' }).fill('zzzz-no-match');
    await expect(page.getByText('No scores match your search.')).toBeVisible();
    await page.locator('.entity-back').click();
    await expect(page.locator('tbody tr').first()).toBeVisible();
    expect(page.url().replace(/#$/, '')).toBe(matrixUrl.replace(/#$/, ''));
    await page.locator('.benchmark-detail-link').first().click();
    await expect(page.locator('.entity-kind')).toHaveText('Benchmark variant');
    await page.locator('.entity-matrix-link').click();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await noOverflow(page);
    const options = page.getByRole('button', { name: /^Options/ });
    if (await options.isVisible()) await options.click();
    await page.getByRole('button', { name: 'Choose benchmarks', exact: true }).click();
    await expect(page.getByRole('dialog').getByRole('checkbox', { checked: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Done', exact: true }).click();
  });
}

test('invalid entity URLs are recoverable', async ({ page }) => {
  await page.goto('./#/models/%E0%A4%A');
  await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible();
  await page.locator('.entity-back').click();
  await expect(page.locator('tbody tr').first()).toBeVisible();
  await page.goto('./#/benchmarks/not-a-real-benchmark');
  await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible();
});


test('wide desktop comparisons keep compact columns and bounded rendering', async ({ page }) => {
  await page.setViewportSize({ width: 2506, height: 1239 });
  await ready(page);
  await page.getByRole('button', { name: 'Choose models', exact: true }).click();
  const choices = page.getByRole('dialog').getByRole('checkbox');
  for (let i = 0; i < 20; i++) await choices.nth(i).check();
  await page.getByRole('button', { name: 'Compare selected models', exact: true }).click();
  await expect(page.locator('.selection-strip button')).toHaveCount(20);
  const modelCount = await page.locator('thead th').count() - 1;
  expect(modelCount).toBeGreaterThanOrEqual(14);
  expect(modelCount).toBeLessThanOrEqual(16);
  const widths = await page.locator('thead th:not(:first-child)').evaluateAll(elements => elements.map(el => el.getBoundingClientRect().width));
  for (const width of widths) expect(width).toBeCloseTo(150, 0);
  expect(await page.locator('tbody td').count()).toBeLessThanOrEqual(50 * 25);
  await noOverflow(page);
  await page.getByRole('button', { name: 'Next models', exact: true }).click();
  await expect(page.locator('thead th')).toHaveCount(20 - modelCount + 1);
  const lastWidths = await page.locator('thead th:not(:first-child)').evaluateAll(elements => elements.map(el => el.getBoundingClientRect().width));
  for (const width of lastWidths) expect(width).toBeCloseTo(150, 0);
  expect(new URL(page.url()).searchParams.has('v')).toBe(false);
  expect(new URL(page.url()).hash).toMatch(/^#\/\?v=b1\./);
  const request = page.waitForRequest(request => request.isNavigationRequest());
  await page.reload();
  expect((await request).url().length).toBeLessThan(200);
  await expect(page.locator('.selection-strip button')).toHaveCount(20);
  await expect(page.locator('thead th')).toHaveCount(modelCount + 1);
});

test('model identity logos appear on model and benchmark reference pages', async ({ page }) => {
  await page.goto('./#/models/claude_opus55');
  await expect(page.locator('h1 .model-identity img')).toBeVisible();
  await page.locator('.entity-score-title a').first().click();
  await expect(page.locator('.entity-kind')).toHaveText('Benchmark variant');
  await expect(page.locator('.entity-score-title .model-identity img').first()).toBeVisible();
  const icons = page.locator('.entity-score-title .model-identity img');
  expect(await icons.evaluateAll(images => images.every(img => (img as HTMLImageElement).complete && (img as HTMLImageElement).naturalWidth > 0))).toBe(true);
});

for (const width of [375, 768, 1422]) {
  test(`${width}px searchable catalogs, exact model matrix and coverage`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('./#/models');
    await expect(page.getByRole('heading', { level: 1, name: 'Models', exact: true })).toBeVisible();
    await expect(page.locator('.catalog-card')).toHaveCount(24);
    await noOverflow(page);
    await page.getByRole('searchbox', { name: 'Search catalog' }).fill('Claude Opus 5.5');
    await expect(page.locator('.catalog-card')).toHaveCount(1);
    await expect(page.locator('.catalog-card .model-brand-icon')).toBeVisible();
    await page.locator('.catalog-card-bottom a').click();
    await expect(page.locator('.model-link').first()).toContainText('Claude Opus 5.5');
    await noOverflow(page);
    await page.getByRole('link', { name: 'Benchmarks', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Benchmark variants' })).toBeVisible();
    await page.getByRole('searchbox', { name: 'Search catalog' }).fill('zzzzz-no-match');
    await expect(page.getByText(/No matches/)).toBeVisible();
    await page.getByRole('button', { name: 'Reset filters' }).click();
    await expect(page.locator('.catalog-card')).toHaveCount(24);
    await noOverflow(page);
    await page.getByRole('link', { name: 'Coverage & evidence', exact: true }).first().click();
    await expect(page.getByRole('heading', { level: 1, name: 'Coverage & evidence' })).toBeVisible();
    await page.locator('.gap-list summary').first().click();
    await expect(page.locator('.gap-list details[open] p')).toBeVisible();
    await expect(page.getByRole('link', { name: 'manifest.json ↓' })).toHaveAttribute('href', /data\/manifest.json$/);
    await noOverflow(page);
    await page.reload();
    await expect(page.getByRole('heading', { level: 1, name: 'Coverage & evidence' })).toBeVisible();
  });
}

for (const width of [375, 1422]) {
  test(`${width}px directory state survives detail navigation, Back and reload`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('./#/models');
    const search = page.getByRole('searchbox', { name: 'Search catalog' });
    await search.fill('Mistral');
    await expect(page.locator('.catalog-card')).toHaveCount(4);
    await page.locator('.catalog-card h2 a').first().click();
    await expect(page.locator('.entity-score').first()).toBeVisible();
    await expect(page.locator('.entity-back')).toHaveText('Back to models');
    await page.goBack();
    await expect(search).toHaveValue('Mistral');
    await page.reload();
    await expect(search).toHaveValue('Mistral');
    await page.getByRole('link', { name: 'Benchmarks', exact: true }).click();
    await expect(search).toHaveValue('');
    await search.fill('GraphWalks');
    await page.locator('.catalog-card h2 a').first().click();
    await expect(page.locator('.entity-score').first()).toBeVisible();
    await page.getByRole('link', { name: 'Back to benchmarks', exact: true }).click();
    await expect(search).toHaveValue('GraphWalks');
    await page.getByRole('link', { name: 'Models', exact: true }).click();
    await expect(search).toHaveValue('Mistral');
    await noOverflow(page);
  });
}

test('matrix search is preserved when navigating immediately, then Back and Forward', async ({ page }) => {
  await ready(page);
  await page.getByRole('searchbox', { name: 'Search models', exact: true }).fill('Gemini');
  await page.getByRole('link', { name: 'Models', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Models', exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('searchbox', { name: 'Search models', exact: true })).toHaveValue('Gemini');
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Models', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Matrix', exact: true }).click();
  await expect(page.getByRole('searchbox', { name: 'Search models', exact: true })).toHaveValue('Gemini');
});
