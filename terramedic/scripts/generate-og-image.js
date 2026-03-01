/**
 * Generate the OG image (static/images/og-image.png) by screenshotting the
 * homepage hero section with Playwright.
 *
 * Prerequisites:
 *   - Dev server running on port 5173 (`yarn dev`)
 *   - Playwright browsers installed (`npx playwright install chromium`)
 *
 * Usage:
 *   node scripts/generate-og-image.js
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { chromium } from '@playwright/test';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = join(__dirname, '..', 'static', 'images', 'og-image.png');
const DEV_SERVER_URL = 'http://localhost:5173';
const VIEWPORT = { width: 1200, height: 630 }; // OG image standard size

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setViewportSize(VIEWPORT);
await page.goto(DEV_SERVER_URL, { waitUntil: 'networkidle' });

await page.evaluate(() => {
  // Hide navbar and warming-stripes accent strip
  const nav = document.querySelector('nav');
  if (nav) nav.style.display = 'none';
  if (nav && nav.nextElementSibling) nav.nextElementSibling.style.display = 'none';

  // Hide tagline and description paragraphs
  document.querySelectorAll('.hero-content p').forEach((p) => (p.style.display = 'none'));

  // Hide CTA button container
  const heroContent = document.querySelector('.hero-content');
  const divs = heroContent.querySelectorAll(':scope > div');
  if (divs.length) divs[divs.length - 1].style.display = 'none';

  // Center text over the dark space above the earth horizon
  if (heroContent) {
    heroContent.style.padding = '0 1rem 25%';
    heroContent.style.display = 'flex';
    heroContent.style.alignItems = 'center';
    heroContent.style.justifyContent = 'center';
  }

  // Scale up the heading
  const h1 = heroContent.querySelector('h1');
  if (h1) {
    h1.style.marginBottom = '0';
    h1.style.transform = 'scale(1.6)';
  }
});

// Wait for video frame to render
await page.waitForTimeout(1500);

await page.screenshot({
  path: OUTPUT_PATH,
  clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height }
});

await browser.close();
console.log(`OG image saved to ${OUTPUT_PATH}`);
