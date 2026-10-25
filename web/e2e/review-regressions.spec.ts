import { expect, test } from '@playwright/test';
import { HOUR, installPriceFixture } from './fixtures/prices';
import { DEFAULT_VIEW, type ViewState } from '../src/state/viewState';

const url = (view: ViewState) => `./#/?v=${encodeURIComponent(JSON.stringify(view))}`;

test('real worker reselects the primary setup after choosing benchmarks, across reload and history', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const view = { ...structuredClone(DEFAULT_VIEW), presetId: 'all_models_oct2026', orientation: 'models-rows' as const, visibleColumnIds: ['terminal_bench_4', 'arena_agent_bash_reliability_20261016', 'arena_agent_confirmed_success_20261016'] };
  await page.goto(url(view));
  await expect(page.getByRole('checkbox', { name: 'Select GPT-6 Astra, max', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Choose benchmarks', exact: true }).click();
  await page.getByRole('searchbox', { name: 'Find a benchmark' }).fill('Agent Arena');
  const selected = page.locator('.column-option').filter({ has: page.getByRole('checkbox', { checked: true }) });
  await expect(selected).toHaveCount(2);
  await selected.first().getByRole('checkbox').uncheck();
  await selected.first().getByRole('checkbox').uncheck();
  await page.getByRole('button', { name: 'Done', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: 'Select GPT-6 Astra, high', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('checkbox', { name: 'Select GPT-6 Astra, high', exact: true })).toBeVisible();
  await page.goBack();
  await page.goBack();
  await expect(page.getByRole('checkbox', { name: 'Select GPT-6 Astra, max', exact: true })).toBeVisible();
  await page.goForward();
  await page.goForward();
  await expect(page.getByRole('checkbox', { name: 'Select GPT-6 Astra, high', exact: true })).toBeVisible();
});

for (const width of [1440, 390]) {
  test(`stale prices require an explicit saved opt-in at ${width}px`, async ({ page }) => {
    await installPriceFixture(page, 49 * HOUR);
    await page.setViewportSize({ width, height: 844 });
    const view = { ...structuredClone(DEFAULT_VIEW), presetId: 'all_models_oct2026', visibleColumnIds: ['terminal_bench_4', 'market:price'], filters: { ...DEFAULT_VIEW.filters, maxInputPricePerMillion: 1000 } };
    await page.goto(url(view));
    await expect(page.getByText(width === 390 ? 'No configurations match these filters.' : 'No configurations match this view', { exact: true })).toBeVisible();
    if (width === 390) await page.getByRole('button', { name: /^Options/ }).click();
    await page.getByRole('button', { name: /^Filters/ }).click();
    await page.getByRole('checkbox', { name: 'Include stale price quotes (historical)', exact: true }).check();
    await page.getByRole('button', { name: 'Apply filters', exact: true }).click();
    await expect(page.getByText('Historical prices included', { exact: true })).toBeVisible();
    if (width === 390) await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    else await expect(page.getByText(/Includes stale quotes/).first()).toBeVisible();
    await page.reload();
    await expect(page.getByText(width === 390 ? 'Historical price quotes included (48+ hours old).' : 'Historical prices included', { exact: true })).toBeVisible();
  });
  test(`reported mobile scores and exact desktop setups at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    // Use the real benchmark ID from the default chooser via its human-readable name.
    await page.goto('./');
    if (width === 390) {
      await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
      await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('Vals Index');
      await page.getByRole('option').first().click();
    }
    await page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true }).fill('Mistral');
    if (width === 390) {
      const reported = page.getByRole('button', { name: /Mistral Large 4, Vals Index: 48.66 %/ });
      await expect(reported).toHaveText('48.66%');
      await expect(reported).toHaveAttribute('data-heat');
      await expect(page.locator('.portrait-model-score [data-other-setups]')).toHaveCount(0);
      await expect(page.locator('.mobile-score-bar')).toHaveCount(1);
      expect(await page.locator('.mobile-score-bar').evaluate(el => (el as HTMLElement).style.width)).toBe('48.66%');
      await reported.click();
      await expect(page.locator('.evidence-record')).toContainText('48.66');
      await expect(page.locator('.evidence-record')).toContainText('Vals AI');
      await page.getByRole('button', { name: 'Close', exact: true }).click();
      await page.reload();
      await expect(reported).toHaveText('48.66%');
      await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
      await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('DeepSWE');
      await page.getByRole('option').first().click();
      await expect(page.getByRole('button', { name: /Mistral Large 4, DeepSWE v1.1: 61.7 %/ })).toHaveText('61.7%');
      await page.goBack();
      await expect(reported).toHaveText('48.66%');
    } else {
      const alternate = page.getByRole('button', { name: /Mistral Large 4, Vals Index: No score for this setup/ });
      await expect(alternate).toHaveText('Other setups (1)');
      await expect(alternate).not.toHaveAttribute('data-heat');
      await expect(alternate).not.toHaveAttribute('data-best');
      await alternate.click();
      await page.locator('.alternative-setup').click();
      await expect(page.locator('.evidence-record')).toContainText('48.66');
    }
  });
}

for (const width of [320, 390, 844]) {
  test(`mobile model scores replace one- and two-setup placeholders at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: width === 844 ? 390 : 844 });
    await page.goto('./');
    await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
    await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('Vals Index');
    await page.getByRole('option').first().click();
    await expect(page.getByRole('button', { name: /Mistral Large 4, Vals Index: 48.66 %/ })).toHaveText('48.66%');
    await expect(page.getByRole('button', { name: /Claude Fable 5.1, Vals Index: 65.8 %/ })).toHaveText('65.8%');
    await expect(page.getByRole('button', { name: /Claude Opus 5.5, Vals Index: 67 %/ })).toHaveText('67%');
    await expect(page.locator('.portrait-model-score [data-other-setups]')).toHaveCount(0);
    const geometry = await page.locator('.portrait-model-card').evaluateAll(cards => cards.map(card => {
      const button = card.querySelector('.score-button')!;
      const value = /^\d/.test(button.textContent ?? '') ? parseFloat(button.textContent!) : null;
      const bar = card.querySelector<HTMLElement>('.mobile-score-bar');
      return { value, bar: bar ? parseFloat(bar.style.width) : null, best: button.hasAttribute('data-best'), height: card.getBoundingClientRect().height };
    }));
    const numeric = geometry.filter(row => row.value !== null);
    expect(numeric.length).toBeGreaterThan(5);
    expect(numeric.map(row => row.value)).toEqual(numeric.map(row => row.value).sort((a, b) => b! - a!));
    expect(geometry.every(row => row.value === row.bar && row.height <= 48)).toBe(true);
    expect(numeric.filter(row => row.best).map(row => row.value)).toEqual(numeric.filter(row => row.value === numeric[0].value).map(row => row.value));
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    await page.screenshot({ path: testInfo.outputPath('reported-scores.png'), animations: 'disabled' });
  });
}
