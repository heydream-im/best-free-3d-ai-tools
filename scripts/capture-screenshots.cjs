// Requires Node.js, Playwright and Google Chrome.
// Usage: node scripts/capture-screenshots.cjs [product-id ...]
// New captures go into an ignored review directory, never over reviewed assets.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = JSON.parse(fs.readFileSync(path.join(root, 'data/screenshots.json'), 'utf8'));
const selected = process.argv.slice(2);
const targets = source.filter(item => !selected.length || selected.includes(item.id));
if (!targets.length || selected.some(id => !source.some(item => item.id === id))) {
  console.error('Unknown product id. See data/screenshots.json for supported ids.');
  process.exit(1);
}
(async () => {
  const out = path.join(root, '.capture-review', new Date().toISOString().replace(/[:.]/g, '-'));
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const results = [];
  async function capture(item) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1,
      locale: 'en-US', reducedMotion: 'reduce'
    });
    const page = await context.newPage();
    const url = item.final_url || item.requested_url;
    try {
      const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(6500); // Allow public page images to appear.
      const title = await page.title();
      if ((response && response.status() >= 400) || /just a moment|access denied/i.test(title)) {
        throw new Error(`Page unavailable: HTTP ${response?.status()}, title=${title}`);
      }
      const file = `${item.id}.jpg`;
      await page.screenshot({ path: path.join(out, file), type: 'jpeg', quality: 85, timeout: 20000 });
      results.push({ id: item.id, requested_url: url, final_url: page.url(), title,
        http_status: response?.status(), file, captured_at: new Date().toISOString(),
        viewport: { width: 1440, height: 1000 }, reviewed: false });
      console.log(`${item.id}: saved for visual review`);
    } catch (error) {
      results.push({ id: item.id, requested_url: url, error: error.message, reviewed: false });
      console.error(`${item.id}: ${error.message}`);
    } finally { await context.close(); }
  }
  try {
    for (let i = 0; i < targets.length; i += 3) {
      await Promise.allSettled(targets.slice(i, i + 3).map(capture));
    }
  } finally {
    await browser.close();
    results.sort((a, b) => targets.findIndex(t => t.id === a.id) - targets.findIndex(t => t.id === b.id));
    fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(results, null, 2) + '\n');
    console.log(`Review images and manifest before updating README assets: ${out}`);
    if (results.some(r => r.error)) process.exitCode = 1;
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
