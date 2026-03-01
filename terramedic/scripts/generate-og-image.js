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

let browser;
try {
  browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize(VIEWPORT);
  await page.goto(DEV_SERVER_URL, { waitUntil: 'networkidle' });

  await page.evaluate(() => {
    // Hide navbar (outside hero, selected by tag)
    const nav = document.querySelector('nav');
    if (nav) {
      const navWrapper = nav.closest('.sticky') || nav.parentElement;
      if (navWrapper) navWrapper.style.display = 'none';
    }

    // Hide elements marked with data-og-hide (tagline, description, CTA)
    document.querySelectorAll('[data-og-hide]').forEach((el) => (el.style.display = 'none'));

    // Restyle hero content container for OG layout
    const heroContent = document.querySelector('[data-og-hero]');
    if (!heroContent) return;

    // Center text over the dark space above the earth horizon
    heroContent.style.padding = '0 1rem 25%';
    heroContent.style.display = 'flex';
    heroContent.style.alignItems = 'center';
    heroContent.style.justifyContent = 'center';

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

  console.log(`OG image saved to ${OUTPUT_PATH}`);
} catch (err) {
  console.error('Failed to generate OG image:', err.message);
  process.exit(1);
} finally {
  if (browser) await browser.close();
}
