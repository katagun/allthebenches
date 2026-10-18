import { test, expect } from '@playwright/test';

test('multiple reports show a numeric range without downloading evidence', async ({ page }) => {
  const evidenceRequests: string[] = [];
  page.on('request', request => { if (/evidence-.*\.json/.test(request.url())) evidenceRequests.push(request.url()); });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('./');
  const score = page.getByRole('button', { name: /Claude Fable 5.1, Terminal-Bench 4.0: Multiple reports:/ });
  await expect(score).toHaveText('55.8–57.9%‡');
  await expect(score).not.toHaveAttribute('data-heat');
  await expect(score).not.toHaveAttribute('data-best');
  expect(evidenceRequests).toHaveLength(0);
  await score.click();
  await expect(page.locator('.evidence-record')).toHaveCount(2);
  await expect(page.locator('.evidence-record').nth(0)).toContainText('55.8');
  await expect(page.locator('.evidence-record').nth(1)).toContainText('57.9');
  expect(evidenceRequests).toHaveLength(1);
});
