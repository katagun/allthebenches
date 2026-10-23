import { test, expect } from '@playwright/test';

test('multiple reports stay unranked without downloading evidence', async ({ page }) => {
  const evidenceRequests: string[] = [];
  page.on('request', request => { if (/evidence-.*\.json/.test(request.url())) evidenceRequests.push(request.url()); });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('./');
  const score = page.getByRole('button', { name: /Claude Fable 5.1, Terminal-Bench 4.0: Disputed result/ });
  await expect(score).toHaveText('Disputed');
  await expect(score).toHaveAttribute('title', /Multiple or disputed reports are unranked/);
  await expect(score).not.toHaveAttribute('data-heat');
  await expect(score).not.toHaveAttribute('data-best');
  expect(evidenceRequests).toHaveLength(0);
  await score.click();
  await expect(page.locator('.evidence-record')).toHaveCount(2);
  await expect(page.locator('.evidence-record').nth(0)).toContainText('55.8');
  await expect(page.locator('.evidence-record').nth(1)).toContainText('57.9');
  expect(evidenceRequests).toHaveLength(1);
});

for (const width of [1440, 390]) {
  test(`every visible numeric score has gradient highlighting at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('./');
    await expect(page.locator('.score-button[data-heat]').first()).toBeVisible();
    const numericScores = page.locator('.score-button:visible').filter({ hasText: /^-?\d/ });
    expect(await numericScores.count()).toBeGreaterThan(0);
    for (const score of await numericScores.all()) {
      await expect(score).toHaveAttribute('data-heat', 'true');
    }
    const blanks = page.locator('.score-button:visible').filter({ hasText: /^—$/ });
    for (const blank of await blanks.all()) await expect(blank).not.toHaveAttribute('data-heat');
  });
}
