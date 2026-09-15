import { chromium } from 'playwright';

const url = 'http://127.0.0.1:9100/';
const widths = [1920, 1280, 1024, 768, 480, 414, 390, 375, 360, 320];

const browser = await chromium.launch();
for (const w of widths) {
  const page = await browser.newPage({ viewport: { width: w, height: 800 } });
  await page.goto(url, { waitUntil: 'networkidle' });
  const result = await page.evaluate(() => {
    const overflow = [];
    document.querySelectorAll('*').forEach(el => {
      const r = el.getBoundingClientRect();
      const sw = el.scrollWidth;
      if (r.right > window.innerWidth + 1 || r.left < -1) {
        overflow.push(`R>${Math.round(r.right)} tag=${el.tagName} cls=${typeof el.className==='string'?el.className:'(svg)'}`);
      }
    });
    // also check if document scrollWidth exceeds innerWidth
    return {
      innerWidth: window.innerWidth,
      docScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      overflow,
    };
  });
  console.log(`WIDTH ${w}: `, JSON.stringify(result));
  await page.close();
}
await browser.close();
