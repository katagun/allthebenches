import { test, expect, type Page } from '@playwright/test';

test.use({ isMobile: true, hasTouch: true });

async function fitsViewport(page: Page) {
  const width = page.viewportSize()!.width;
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
  // Portaled, fixed dialogs can overflow without changing the document width.
  for (const dialog of await page.getByRole('dialog').all()) {
    const overflow = await dialog.evaluate(element => {
      const box = element.getBoundingClientRect();
      return { left: box.left, right: box.right, content: element.scrollWidth - element.clientWidth };
    });
    expect(overflow.left).toBeGreaterThanOrEqual(-1);
    expect(overflow.right).toBeLessThanOrEqual(width + 1);
    expect(overflow.content).toBeLessThanOrEqual(1);
  }
}

for (const [width, height] of [[320, 740], [375, 812], [390, 844], [430, 932], [768, 1024], [844, 390], [1024, 768]]) {
  test(`${width}x${height}: benchmark picker fits while browsing, searching, selecting and rotating`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height });
    await page.goto('./');
    const picker = page.getByRole('button', { name: 'Choose benchmark', exact: true });
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await picker.click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath('benchmark-picker.png') });
    await fitsViewport(page);
    expect(await page.getByRole('searchbox', { name: 'Search benchmarks' }).evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
    const list = page.getByRole('listbox', { name: 'Benchmarks', exact: true });
    expect(await list.evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(1);
    await page.getByRole('option').last().scrollIntoViewIfNeeded();
    await expect(page.getByRole('option').last()).toBeInViewport();
    await fitsViewport(page);
    await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('GraphWalks');
    await expect(page.getByRole('option').first()).toBeVisible();
    await fitsViewport(page);
    const title = await page.getByRole('option').first().locator('strong').innerText();
    await page.getByRole('option').first().click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect(picker.locator('strong')).toHaveText(title);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    await picker.click();
    await page.setViewportSize({ width: height, height: width });
    await fitsViewport(page);
    await page.setViewportSize({ width, height });
    await fitsViewport(page);
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await expect(picker).toBeInViewport();
  });
}

test('phone search fields avoid focus zoom and long benchmark metadata wraps', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto('./');
  await page.getByRole('button', { name: 'Choose benchmark', exact: true }).click();
  const search = page.getByRole('searchbox', { name: 'Search benchmarks' });
  await expect(search).toBeFocused();
  // iOS zooms focused text fields below 16px; desktop browser emulation does not.
  expect.soft(await search.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
  // Exercise unbroken version/metric identifiers as the catalog grows.
  await page.getByRole('option').first().locator('span').evaluate(el => {
    el.textContent = 'benchmark_version_with_a_very_long_unbroken_identifier_'.repeat(4);
  });
  await page.screenshot({ path: testInfo.outputPath('long-benchmark-label.png') });
  await fitsViewport(page);
  expect(await page.getByRole('listbox').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(1);
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  await page.getByRole('button', { name: 'Options', exact: true }).click();
  await page.getByRole('button', { name: 'Choose benchmarks', exact: true }).click();
  const benchmarkSearch = page.getByRole('searchbox', { name: 'Find a benchmark' });
  await expect(benchmarkSearch).toBeVisible();
  expect(await benchmarkSearch.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
  await fitsViewport(page);
});
