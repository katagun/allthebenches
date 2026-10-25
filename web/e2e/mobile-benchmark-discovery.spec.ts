import { test, expect } from '@playwright/test';

test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });

test('default mobile picker exposes every published benchmark, including future additions', async ({ page }) => {
  const response = await page.request.get('data/catalog.json');
  expect(response.ok()).toBe(true);
  const catalog = await response.json() as { benchmarks: { name: string }[] };
  await page.goto('./');
  await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
  const options = page.getByRole('option');
  await expect(options).toHaveCount(catalog.benchmarks.length);
  expect(await options.locator('strong').allTextContents()).toEqual(catalog.benchmarks.map(benchmark => benchmark.name));
});

for (const benchmarkId of ['bullshitbench_v2_avg_grade', 'arena_text_overall_bt_20261015', 'qwen3_base_mgsm']) {
  test(`mobile discovery opens scored results outside Frontier: ${benchmarkId}`, async ({ page }) => {
    const response = await page.request.get('data/catalog.json');
    const catalog = await response.json() as {
      benchmarks: { id: string; name: string }[];
      presets: { id: string; benchmark_ids: string[] }[];
    };
    expect(catalog.presets.find(preset => preset.id === 'frontier_oct2026')!.benchmark_ids).not.toContain(benchmarkId);
    const benchmark = catalog.benchmarks.find(item => item.id === benchmarkId)!;
    await page.goto('./');
    const picker = page.getByRole('button', { name: 'Choose benchmark', exact: true });
    await picker.click();
    await page.getByRole('searchbox', { name: 'Search benchmarks', exact: true }).fill(benchmark.name);
    await page.getByRole('option').filter({ has: page.locator('strong', { hasText: benchmark.name }) }).first().click();
    await expect(picker).toContainText(benchmark.name);
    await expect(page.locator('.mobile-score-bar').first()).toBeVisible();
    await page.reload();
    await expect(picker).toContainText(benchmark.name);
    await expect(page.locator('.mobile-score-bar').first()).toBeVisible();
  });
}
