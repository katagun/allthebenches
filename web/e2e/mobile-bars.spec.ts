import { test, expect } from '@playwright/test';

// Bar tracks must measure identically across cards so percentages compare;
// score buttons keep a fixed width so long ranges cannot steal track space
// or wrap onto a second line.
async function expectAlignedBars(page, label: string) {
  const geometry = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('.portrait-model-card')];
    const tracks = cards.map(el => { const t = el.querySelector('.mobile-score-track'); return t ? Math.round(t.getBoundingClientRect().width) : -1; }).filter(w => w >= 0);
    const overflow = [...document.querySelectorAll('.portrait-model-score .score-button')].map(el => el.scrollWidth - el.clientWidth);
    const heights = cards.map(el => Math.round(el.getBoundingClientRect().height));
    return { tracks: [...new Set(tracks)], overflow: Math.max(...overflow), maxH: Math.max(...heights) };
  });
  expect(geometry.tracks, `${label}: uniform track widths`).toHaveLength(1);
  expect(geometry.overflow, `${label}: no clipped score text`).toBeLessThanOrEqual(1);
  expect(geometry.maxH, `${label}: one-line cards`).toBeLessThanOrEqual(48);
}

async function selectBenchmark(page, name: string) {
  await page.locator('.portrait-benchmark-picker').click();
  await page.getByRole('searchbox', { name: 'Search benchmarks' }).fill(name);
  await expect(page.getByRole('option').first()).toBeVisible();
  await page.getByRole('option').first().click();
  await page.waitForTimeout(300);
}

for (const width of [320, 390]) {
  test(`${width}px bar tracks share one geometry`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto('./');
    await expect(page.locator('.portrait-model-card').first()).toBeVisible();
    await page.waitForTimeout(300);
    await expectAlignedBars(page, `default ${width}px`);
    // Vals Index is range-heavy; Terminal-Bench 4.0 has the longest wraps seen.
    for (const bench of ['Vals Index', 'Terminal-Bench 4.0']) {
      await selectBenchmark(page, bench);
      await expectAlignedBars(page, `${bench} ${width}px`);
    }
  });
}
