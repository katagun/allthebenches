import { test, expect, type Page } from '@playwright/test';

async function ready(page: Page, matrix = true) {
  await page.goto('./');
  if (page.viewportSize()!.width <= 1100) {
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    if (matrix) await showMatrix(page);
  } else await expect(page.locator('tbody tr').first()).toBeAttached();
  await expect(page.getByText('Updating comparison…', { exact: false })).toHaveCount(0);
}

async function options(page: Page) {
  if (page.viewportSize()!.width > 1100) return;
  if (await page.locator('.mobile-settings[data-state=open]').count()) {
    await page.getByRole('button', { name: 'Done', exact: true }).click();
  } else await page.getByRole('button', { name: /^Options/ }).click();
}
async function advanced(page: Page) {
  if (page.viewportSize()!.width <= 1100 && !await page.locator('.mobile-advanced[open]').count()) await page.locator('.mobile-advanced summary').click();
}
async function showMatrix(page: Page) {
  await options(page);
  await advanced(page);
  await page.getByRole('button', { name: 'Matrix view', exact: true }).click();
  await expect(page.locator('thead')).toBeVisible();
}
async function control(page: Page, name: string) {
  if (page.viewportSize()!.width <= 1100 && !await page.locator('.mobile-settings[data-state=open]').count()) await options(page);
  await page.getByRole('button', { name, exact: true }).click();
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
        await options(page);
        await advanced(page);
        await page.getByRole('combobox', { name: 'Table orientation' }).click();
        await page.getByRole('option', { name: 'Model rows', exact: true }).click();
        await options(page);
      }
      await noOverflow(page);
      const card = await page.locator('.table-card').boundingBox();
      expect(card!.y).toBeLessThan(320);
      expect(card!.height).toBeGreaterThan(844 * 0.5);
      const header = await page.locator('thead').boundingBox();
      expect(header!.height).toBeLessThan(190);
      await expect(page.getByRole('button', { name: 'Options', exact: true })).toHaveAttribute('aria-expanded', 'false');
      // All-model coverage provides enough rows to require vertical scrolling.
      await control(page, 'All models');
      if (page.viewportSize()!.width <= 1100) await options(page);
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
      await options(page);
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
  test(`${width}px optional dense matrix fits available width`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await ready(page);
    await options(page);
    await advanced(page);
    await page.getByRole('button', { name: 'Dense matrix', exact: true }).click();
    await options(page);
    await expect(page.locator('thead th')).toHaveCount(5);
    const scroll = page.locator('[data-slot="table-container"]');
    expect(await scroll.evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(1);
    await noOverflow(page);
  });
}

for (const width of [390, 1422]) {
  test(`${width}px choose models, compare and restore shared state`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await ready(page);
    await control(page, 'Choose models');
    await page.getByRole('searchbox', { name: 'Find a model' }).fill('Claude 3');
    const choices = page.getByRole('dialog').getByRole('checkbox');
    await choices.nth(0).check();
    await choices.nth(1).check();
    await page.getByRole('button', { name: 'Compare selected models', exact: true }).click();
    await expect(page.locator('.selection-strip button')).toHaveCount(2);
    if (width <= 1100) await options(page);
    await expect(page.locator('thead th')).toHaveCount(3);
    await noOverflow(page);
    await page.reload();
    if (width <= 1100) await showMatrix(page);
    await expect(page.locator('thead th')).toHaveCount(3);
    if (width <= 1100) {
      await options(page);
      await expect(page.locator('.selection-strip button')).toHaveCount(2);
      await page.getByRole('button', { name: 'Show all rows', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Compare 2 selected', exact: true })).toBeVisible();
      return;
    }
    await expect(page.getByRole('button', { name: 'Compare', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await page.getByRole('button', { name: 'Explore', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Explore', exact: true })).toHaveAttribute('aria-pressed', 'true');
  });
}

test('picker permits more than five selections and discards cancelled edits', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  await control(page, 'Choose models');
  const choices = page.getByRole('dialog').getByRole('checkbox');
  for (let i = 0; i < 8; i++) await choices.nth(i).check();
  await expect(choices.nth(7)).toBeChecked();
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await expect(page.locator('.selection-strip')).toHaveCount(0);
  await control(page, 'Choose models');
  await expect(page.getByRole('button', { name: 'Compare selected models', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await page.getByRole('button', { name: 'Choose benchmarks', exact: true }).click();
  await page.getByRole('searchbox', { name: 'Find a benchmark' }).fill('GraphWalks');
  await expect(page.locator('.column-group').first()).toContainText('GraphWalks');
  await noOverflow(page);
});

for (const width of [390, 768, 1422]) {
  test(`${width}px model and benchmark pages, evidence and matrix return`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await ready(page);
    await control(page, 'All models');
      if (page.viewportSize()!.width <= 1100) await options(page);
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
    if (width <= 1100) await showMatrix(page);
    await expect(page.locator('tbody tr').first()).toBeVisible();
    expect(page.url().replace(/#$/, '')).toBe(matrixUrl.replace(/#$/, ''));
    await page.locator('.benchmark-detail-link').first().click();
    await expect(page.locator('.entity-kind')).toHaveText('Benchmark variant');
    await page.getByRole('link', { name: 'View this benchmark in the matrix →', exact: true }).click();
    if (width <= 1100) await showMatrix(page);
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await noOverflow(page);
    if (width <= 1100) await options(page);
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
  await control(page, 'Choose models');
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
    if (width <= 1100) await options(page);
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
  await page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true }).fill('Gemini');
  await page.getByRole('link', { name: 'Models', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Models', exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true })).toHaveValue('Gemini');
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Models', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Matrix', exact: true }).click();
  await expect(page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true })).toHaveValue('Gemini');
});

for (const theme of ['system', 'class', 'light']) {
  test(`portrait ${theme}: heatmap scores have readable resting and interactive contrast`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ colorScheme: theme === 'system' ? 'dark' : 'light' });
    await ready(page, false);
    if (theme === 'class') await page.evaluate(() => document.documentElement.classList.add('dark'));
    const scores = page.locator('.portrait-model-score .score-button[data-heat]');
    await expect(scores.first()).toBeVisible();
    for (const interaction of ['rest', 'hover', 'focus']) {
      for (const score of await scores.all()) {
        if (interaction === 'hover') await score.hover();
        if (interaction === 'focus') { await page.mouse.move(0, 0); await page.keyboard.press('Tab'); await score.focus(); }
        const contrast = await score.evaluate(element => {
          const canvas = document.createElement('canvas');
          canvas.width = canvas.height = 1;
          const context = canvas.getContext('2d')!;
          const paint = (color: string) => { context.fillStyle = color; context.fillRect(0, 0, 1, 1); };
          const luminance = () => {
            const rgb = [...context.getImageData(0, 0, 1, 1).data].slice(0, 3).map(value => {
              const c = value / 255;
              return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
            });
            return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
          };
          const ancestors: Element[] = [];
          for (let parent = element.parentElement; parent; parent = parent.parentElement) ancestors.unshift(parent);
          paint('white');
          for (const parent of ancestors) paint(getComputedStyle(parent).backgroundColor);
          const style = getComputedStyle(element);
          paint(style.backgroundColor);
          const heat = getComputedStyle(element, '::before');
          context.globalAlpha = Number(heat.opacity);
          paint(heat.backgroundColor);
          context.globalAlpha = 1;
          const background = luminance();
          paint(style.color);
          const text = luminance();
          return (Math.max(text, background) + .05) / (Math.min(text, background) + .05);
        });
        expect(contrast).toBeGreaterThanOrEqual(4.5);
      }
    }
  });
}

for (const theme of ['system', 'class']) {
  for (const orientation of ['benchmarks', 'models']) {
    test(`dark ${theme} ${orientation}: score hover and focus retain readable contrast`, async ({ page }) => {
      await page.setViewportSize({ width: 1422, height: 900 });
      await page.emulateMedia({ colorScheme: theme === 'system' ? 'dark' : 'light' });
      await ready(page);
      if (theme === 'class') await page.evaluate(() => document.documentElement.classList.add('dark'));
      if (orientation === 'models') {
        await advanced(page);
        await page.getByRole('combobox', { name: 'Table orientation' }).click();
        await page.getByRole('option', { name: 'Model rows', exact: true }).click();
      }
      const score = page.locator('.score-button[data-heat]').first();
      await expect(score).toBeVisible();
      for (const interaction of ['hover', 'focus']) {
        if (interaction === 'hover') await score.hover();
        else { await page.mouse.move(0, 0); await page.keyboard.press('Tab'); await score.focus(); }
        if (interaction === 'focus') expect(await score.evaluate(element => element.matches(':focus-visible'))).toBe(true);
        const contrast = await score.evaluate(element => {
          const style = getComputedStyle(element);
          const canvas = document.createElement('canvas');
          canvas.width = canvas.height = 1;
          const context = canvas.getContext('2d')!;
          const luminance = (color: string) => {
            context.clearRect(0, 0, 1, 1); context.fillStyle = color; context.fillRect(0, 0, 1, 1);
            const rgb = [...context.getImageData(0, 0, 1, 1).data].slice(0, 3).map(v => {
              const c = v / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
            });
            return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
          };
          const text = luminance(style.color), background = luminance(style.backgroundColor);
          return (Math.max(text, background) + .05) / (Math.min(text, background) + .05);
        });
        expect(contrast).toBeGreaterThanOrEqual(4.5);
      }
    });
  }
}

test('portrait cards switch benchmarks and keep evidence, model details, selection, and missing scores available', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page, false);
  const cards = page.locator('.portrait-model-card');
  await expect(page.locator('.portrait-comparison')).toBeVisible();
  await expect(page.locator('.portrait-comparison tbody')).toHaveCount(0);
  await expect(cards.first()).toBeVisible();
  const heatedScore = page.locator('.portrait-model-score .score-button[data-heat]').first();
  await expect(heatedScore).toBeVisible();
  expect(await heatedScore.evaluate(button => { const parent = getComputedStyle(button.parentElement!); return parent.position === 'relative' && parent.isolation === 'isolate'; })).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('portrait-cards-390x844.png'), fullPage: false });

  const picker = page.locator('.portrait-benchmark-picker');
  const originalTitle = await picker.locator('strong').innerText();
  const originalUrl = page.url();
  await picker.click();
  const search = page.getByRole('searchbox', { name: 'Search benchmarks' });
  await search.fill('GraphWalks');
  await expect(page.getByRole('option').first()).toBeVisible();
  await expect(picker.locator('strong')).toHaveText(originalTitle);
  const newBenchmark = await page.getByRole('option').first().locator('strong').innerText();
  await page.getByRole('option').first().click();
  await expect(picker.locator('strong')).toHaveText(newBenchmark);
  expect(page.url()).not.toBe(originalUrl);
  await page.reload();
  await expect(picker.locator('strong')).toHaveText(newBenchmark);
  await page.setViewportSize({ width: 844, height: 390 });
  await expect(page.locator('.portrait-comparison')).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.portrait-comparison')).toBeVisible();
  await expect(page.locator('.portrait-benchmark-picker strong')).toHaveText(newBenchmark);

  const evidenceScore = page.locator('.portrait-model-card .score-button').first();
  await evidenceScore.click();
  await expect(page.getByRole('heading', { name: 'Result evidence' })).toBeVisible();
  await expect(page.getByText('Configuration', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close' }).click();

  const selectedModel = page.locator('.portrait-model-card .model-link').first();
  const modelName = (await selectedModel.innerText()).trim();
  await selectedModel.click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(modelName);
  await page.locator('.entity-back').click();
  await expect(page.locator('.portrait-comparison')).toBeVisible();
  await options(page);
  const hideEmpty = page.getByLabel('Hide rows empty on this page');
  if (await hideEmpty.isChecked()) await hideEmpty.uncheck();
  await options(page);
  await expect(page.locator('.portrait-model-card .score-button.missing').first()).toBeVisible();
  await options(page);
  await advanced(page);
        await page.getByRole('combobox', { name: 'Table orientation' }).click();
  await page.getByRole('option', { name: 'Model rows', exact: true }).click();
  await options(page);
  await expect(page.locator('thead')).toBeVisible();
  await expect(page.locator('.portrait-comparison')).toBeHidden();
});

test('landscape uses model rows and desktop remains a matrix', async ({ page }) => {
  await page.setViewportSize({ width: 844, height: 390 });
  await ready(page, false);
  await expect(page.locator('.portrait-model-card').first()).toBeVisible();
  await expect(page.locator('table')).toHaveCount(0);
  await noOverflow(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.locator('thead')).toBeVisible();
  await noOverflow(page);
});

test('benchmark rows stay compact with linked names and separate sorting', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await ready(page);
  await expect(page.getByText('About benchmark', { exact: true })).toHaveCount(0);
  const label = page.locator('tbody .benchmark-detail-link').first();
  await expect(label).toHaveAttribute('href', /benchmarks/);
  const firstRow = page.locator('tbody tr').first();
  expect((await firstRow.boundingBox())!.height).toBeLessThanOrEqual(48);
  await label.focus();
  await expect(page.getByRole('tooltip')).toContainText('is better');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('tooltip')).toHaveCount(0);
  await firstRow.getByRole('button', { name: /^Sort by/ }).click();
  await expect(page.locator('table')).toBeVisible();
  await expect(page.locator('.entity-kind')).toHaveCount(0);
  await page.locator('tbody .benchmark-detail-link').first().click();
  await expect(page.locator('.entity-kind')).toHaveText('Benchmark variant');
});

test('expanded catalog keeps categories and numeric scores inside compact desktop bounds', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await ready(page);
  await control(page, 'All models');
      if (page.viewportSize()!.width <= 1100) await options(page);
  await expect(page.getByText('Updating comparison…', { exact: false })).toHaveCount(0);
  await expect(page.locator('.results-caption').first()).toContainText('configurations');
  expect((await page.locator('.category-nav').boundingBox())!.height).toBeLessThanOrEqual(44);
  expect(await page.locator('.score-button').evaluateAll(buttons => buttons.filter(button => /^[-\d]/.test(button.textContent ?? '') && button.scrollWidth > button.clientWidth + 1).length)).toBe(0);
  await noOverflow(page);
});

test('cold matrix renders without evidence downloads and lazy evidence remains accessible', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => { if (request.url().includes('/data/')) requests.push(request.url()); });
  await page.route('**/data/details.json', route => route.abort());
  await page.route('**/data/results.json', route => route.abort());
  await ready(page);
  expect(requests.filter(url => url.endsWith('/comparison.json'))).toHaveLength(1);
  expect(requests.some(url => /evidence-.*\.json/.test(url))).toBe(false);
  await page.locator('.score-button[data-heat]:not([data-other-setups])').first().click();
  await expect(page.getByRole('heading', { name: 'Result evidence', exact: true })).toBeVisible();
  await expect(page.locator('.evidence-record').first()).toBeVisible();
  expect(requests.filter(url => /evidence-.*\.json/.test(url))).toHaveLength(1);
});

test('Mistral missing cells link to other setups without substituting their scores', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await ready(page);
  await page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true }).fill('Mistral');
  const alternate = page.getByRole('button', { name: /Mistral Large 4, Vals Index: No score for this setup/ });
  await expect(alternate).toHaveText('Other setups (1)');
  await expect(alternate).toHaveAttribute('title', /Results exist in other configurations/);
  await expect(alternate).not.toHaveAttribute('data-heat');
  await expect(alternate).not.toHaveAttribute('data-best');
  await alternate.click();
  await expect(page.getByRole('heading', { name: 'Results in other configurations (1)' })).toBeVisible();
  await page.locator('.alternative-setup').click();
  await expect(page.locator('.evidence-record')).toContainText('48.66');
  await expect(page.getByRole('heading', { name: 'Sources', exact: true })).toBeVisible();
});
