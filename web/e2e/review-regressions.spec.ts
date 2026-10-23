import { expect, test } from '@playwright/test';
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
    await page.clock.setFixedTime(new Date('2026-10-22T12:00:00Z'));
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
  test(`alternate setups stay uncolored and unranked at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    // Use the real benchmark ID from the default chooser via its human-readable name.
    await page.goto('./');
    if (width === 390) {
      await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
      await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('Vals Index');
      await page.getByRole('option').first().click();
    }
    await page.getByRole('searchbox', { name: 'Search models, labs, or benchmarks', exact: true }).fill('Mistral');
    const alternate = page.getByRole('button', { name: /Mistral Large 4, Vals Index: No score for this setup/ });
    await expect(alternate).toHaveText('Other setups (1)');
    await expect(alternate).not.toHaveAttribute('data-heat');
    await expect(alternate).not.toHaveAttribute('data-best');
    if (width === 390) await expect(page.locator('.portrait-model-card').filter({ has: alternate }).locator('.mobile-score-bar')).toHaveCount(0);
    await alternate.click();
    await page.locator('.alternative-setup').click();
    await expect(page.locator('.evidence-record')).toContainText('48.66');
  });
}
