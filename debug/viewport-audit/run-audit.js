const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const target = 'file:///E:/GitHub/910cpr-class-landers/docs/index.html';
  const outDir = 'E:/GitHub/910cpr-class-landers/debug/viewport-audit';
  fs.mkdirSync(outDir, { recursive: true });
  const viewports = [
    { name: 'mobile390', width: 390, height: 844 },
    { name: 'tablet768', width: 768, height: 1024 },
    { name: 'desktop1440', width: 1440, height: 900 },
  ];
  const browser = await chromium.launch({ headless: true });
  const report = [];
  for (const vp of viewports) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto(target, { waitUntil: 'load' });
    await page.waitForTimeout(400);

    const normal = await page.evaluate(() => {
      function btn(text){ return [...document.querySelectorAll('a,button')].find(el => (el.textContent||'').trim()===text) || null; }
      function rect(el){ if(!el) return null; const r=el.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:r.width,height:r.height}; }
      function vis(r,vh,vw){ return !!r && r.bottom>0 && r.top<vh && r.right>0 && r.left<vw; }
      const vh=window.innerHeight, vw=window.innerWidth;
      const h1 = document.querySelector('h1');
      const findR = rect(btn('Find a Class'));
      const groupR = rect(btn('Request Group Training'));
      const callR = rect(btn('Call 910-395-5193'));
      const finder = document.querySelector('#class-finder');
      const finderR = rect(finder);
      const hero = document.querySelector('.home-hero');
      const heroR = rect(hero);
      return {
        title: document.title,
        h1: h1 ? h1.textContent.trim() : null,
        viewport: { w: vw, h: vh },
        ctasVisible: { find: vis(findR,vh,vw), group: vis(groupR,vh,vw), call: vis(callR,vh,vw) },
        ctaRects: { find: findR, group: groupR, call: callR },
        finderTop: finderR ? finderR.top : null,
        finderVisibleAboveFold: !!finderR && finderR.top < vh,
        heroHeight: heroR ? heroR.height : null
      };
    });

    await page.screenshot({ path: path.join(outDir, `${vp.name}-normal.png`), fullPage: false });

    await page.route('**/data/public_schedule.json', route => route.abort());
    await page.route('**/public_schedule.json', route => route.abort());
    await page.route('**/data/schedule_future.json', route => route.abort());
    await page.reload({ waitUntil: 'load' });
    await page.waitForTimeout(700);

    const failure = await page.evaluate(() => {
      const finder = document.querySelector('[data-home-sections]');
      const txt = finder ? (finder.textContent || '').replace(/\s+/g,' ').trim() : '';
      const wraps = document.querySelectorAll('.home-status, .home-jumps, .hero').length;
      return {
        hasFallbackMessage: /Live schedule unavailable/i.test(txt),
        hasHubLinks: /BLS/.test(txt) && /ACLS/.test(txt) && /PALS/.test(txt),
        snippet: txt.slice(0, 220),
        structureBlocks: wraps
      };
    });

    await page.screenshot({ path: path.join(outDir, `${vp.name}-failure.png`), fullPage: false });
    report.push({ viewport: vp, normal, failure });
    await page.close();
  }
  await browser.close();
  const outJson = path.join(outDir, 'report.json');
  fs.writeFileSync(outJson, JSON.stringify(report, null, 2));
  console.log(outJson);
})();
