const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright');

const root = 'E:/GitHub/910cpr-class-landers/docs';
const outDir = 'E:/GitHub/910cpr-class-landers/debug/viewport-audit';
fs.mkdirSync(outDir, { recursive: true });

function contentType(filePath){
  const ext = path.extname(filePath).toLowerCase();
  return ({'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.ico':'image/x-icon'})[ext] || 'application/octet-stream';
}

function safeJoin(base, target){
  const p = path.normalize(path.join(base, target));
  if (!p.startsWith(path.normalize(base))) return null;
  return p;
}

(async () => {
  const edgeCandidates = [
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe'
  ];
  const edgePath = edgeCandidates.find(p => fs.existsSync(p));
  if (!edgePath) throw new Error('Microsoft Edge executable not found');

  const server = http.createServer((req,res)=>{
    const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
    const rel = urlPath === '/' ? '/index.html' : urlPath;
    const filePath = safeJoin(root, rel);
    if (!filePath || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.statusCode = 404; res.end('Not found'); return;
    }
    res.setHeader('Content-Type', contentType(filePath));
    fs.createReadStream(filePath).pipe(res);
  });

  await new Promise(resolve => server.listen(4173, '127.0.0.1', resolve));

  const browser = await chromium.launch({ headless: true, executablePath: edgePath });
  const viewports = [
    { name: 'mobile390', width: 390, height: 844 },
    { name: 'tablet768', width: 768, height: 1024 },
    { name: 'desktop1440', width: 1440, height: 900 },
  ];
  const report = [];

  for (const vp of viewports) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    const normal = await page.evaluate(() => {
      function btn(text){ return [...document.querySelectorAll('a,button')].find(el => (el.textContent||'').trim()===text) || null; }
      function rect(el){ if(!el) return null; const r=el.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:r.width,height:r.height}; }
      function vis(r,vh,vw){ return !!r && r.bottom>0 && r.top<vh && r.right>0 && r.left<vw; }
      const vh=window.innerHeight, vw=window.innerWidth;
      const h1 = document.querySelector('h1');
      const findR = rect(btn('Find a Class'));
      const groupR = rect(btn('Request Group Training'));
      const callR = rect(btn('Call 910-395-5193'));
      const finderR = rect(document.querySelector('#class-finder'));
      const heroR = rect(document.querySelector('.home-hero'));
      return {
        h1: h1 ? h1.textContent.trim() : null,
        ctasVisible: { find: vis(findR,vh,vw), group: vis(groupR,vh,vw), call: vis(callR,vh,vw) },
        ctaRects: { find: findR, group: groupR, call: callR },
        finderTop: finderR ? finderR.top : null,
        finderVisibleAboveFold: !!finderR && finderR.top < vh,
        heroHeight: heroR ? heroR.height : null,
      };
    });
    await page.screenshot({ path: path.join(outDir, `${vp.name}-normal-http.png`), fullPage: false });

    await page.route('**/data/public_schedule.json', route => route.abort());
    await page.route('**/public_schedule.json', route => route.abort());
    await page.route('**/data/schedule_future.json', route => route.abort());
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(700);
    const failure = await page.evaluate(() => {
      const finder = document.querySelector('[data-home-sections]');
      const txt = finder ? (finder.textContent || '').replace(/\s+/g,' ').trim() : '';
      return {
        hasFallbackMessage: /Live schedule unavailable/i.test(txt),
        hasHubLinks: /BLS/.test(txt) && /ACLS/.test(txt) && /PALS/.test(txt),
        snippet: txt.slice(0, 220)
      };
    });
    await page.screenshot({ path: path.join(outDir, `${vp.name}-failure-http.png`), fullPage: false });

    report.push({ viewport: vp, normal, failure });
    await page.close();
  }

  await browser.close();
  await new Promise(resolve => server.close(resolve));
  const outJson = path.join(outDir, 'report-http.json');
  fs.writeFileSync(outJson, JSON.stringify(report, null, 2));
  console.log(outJson);
})();
