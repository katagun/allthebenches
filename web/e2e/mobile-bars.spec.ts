import { test, expect } from '@playwright/test';

// Bar tracks must measure identically across cards so percentages compare;
// score buttons keep a fixed width so long ranges cannot steal track space.
async function expectAlignedBars(page, label: string) {
  const geometry = await page.evaluate(() => {
    const tracks = [...document.querySelectorAll('.mobile-score-track')].map(el => Math.round(el.getBoundingClientRect().width));
    const overflow = [...document.querySelectorAll('.portrait-model-score .score-button')].map(el => el.scrollWidth - el.clientWidth);
    return { tracks: [...new Set(tracks)], overflow: Math.max(...overflow) };
  });
  expect(geometry.tracks, `${label}: uniform track widths`).toHaveLength(1);
  expect(geometry.overflow, `${label}: no clipped score text`).toBeLessThanOrEqual(1);
}

for (const width of [320, 390]) {
  test(`${width}px bar tracks share one geometry`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto('./');
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await page.waitForTimeout(300);
    await expectAlignedBars(page, `default ${width}px`);
    await page.locator('.portrait-benchmark-picker').click();
    await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill('Vals Index');
    await expect(page.getByRole('option').first()).toBeVisible();
    await page.getByRole('option').first().click();
    await page.waitForTimeout(300);
    await expectAlignedBars(page, `vals ${width}px`);
  });
}
