const { chromium } = require('/Users/atul/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');

const url = 'http://127.0.0.1:9100/';
const widths = [1920, 1280, 1024, 768, 480, 414, 390, 375, 360, 320];

(async () => {
  const browser = await chromium.launch();
  for (const w of widths) {
    const page = await browser.newPage({ viewport: { width: w, height: 800 } });
    await page.goto(url, { waitUntil: 'networkidle' });
    const result = await page.evaluate(() => {
      const overflow = [];
      function isClipped(el) {
        let n = el.parentElement;
        while (n) {
          const s = getComputedStyle(n);
          if (s.overflowX === 'hidden' || s.overflow === 'hidden' || s.overflowX === 'clip') return true;
          n = n.parentElement;
        }
        return false;
      }
      document.querySelectorAll('*').forEach(el => {
        const r = el.getBoundingClientRect();
        if ((r.right > window.innerWidth + 1 || r.left < -1) && !isClipped(el)) {
          overflow.push(`right=${Math.round(r.right)} tag=${el.tagName} cls=${typeof el.className==='string'?el.className:'(svg)'}`);
        }
      });
      return {
        innerWidth: window.innerWidth,
        docScrollWidth: document.documentElement.scrollWidth,
        bodyScrollWidth: document.body.scrollWidth,
        overflow,
      };
    });
    console.log(`WIDTH ${w}: docSW=${result.docScrollWidth} bodySW=${result.bodyScrollWidth} overflow=${result.overflow.length}`);
    result.overflow.slice(0, 4).forEach(o => console.log(`   -> ${o}`));
    await page.close();
  }
  await browser.close();
})();
