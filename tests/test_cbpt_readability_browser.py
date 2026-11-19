"""Read-only local rendering; requests are fulfilled from this candidate only."""
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

CONTRAST = r"""el => {
 const rgba=s=>(s.match(/[\d.]+/g)||[]).map(Number);
 const lum=rgb=>rgb.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4)}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 let node=el,bg;
 while(node){const c=rgba(getComputedStyle(node).backgroundColor);if(c.length>=3&&(c.length<4||c[3]===1)){bg=c;break;}node=node.parentElement;}
 bg=bg||[255,255,255];const style=getComputedStyle(el),fg=rgba(style.color),a=lum(fg),b=lum(bg);
 return {ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),color:style.color,background:bg,text:el.textContent.trim().slice(0,45)};
}"""

class CBPTReadabilityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(channel='chrome',headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def open(self,theme,width):
  context=self.browser.new_context(viewport={'width':width,'height':900},color_scheme=theme)
  self.addCleanup(context.close)
  def serve(route):
   path=urlparse(route.request.url).path
   file=ROOT/'docs'/('cbpt.html' if path=='/cbpt' else path.lstrip('/'))
   if route.request.method!='GET':route.abort();return
   if file.is_file():route.fulfill(path=str(file))
   else:route.fulfill(status=200,body='')
  context.route('**/*',serve)
  page=context.new_page();page.goto('https://www.910cpr.com/cbpt',wait_until='networkidle')
  self.assertEqual(page.locator('html').get_attribute('data-theme'),theme)
  return page
 def check(self,locator):
  for el in locator.all():
   data=el.evaluate(CONTRAST);self.assertGreaterEqual(data['ratio'],4.5,str(data))
 def test_mobile_desktop_both_themes_and_interaction_states(self):
  for theme in ('light','dark'):
   for width in (390,1440):
    with self.subTest(theme=theme,width=width):
     page=self.open(theme,width)
     self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
     selector='.partner h3,.partner small,.partner-links a,.registration h3,.registration p,.registration .cta,.pressitem small,.pressitem strong,.share-actions a,.share-actions button,.hero .cta'
     self.check(page.locator(selector))
     for el in page.locator('.cta,.share-actions a,.share-actions button,.partner-links a').all():
      if not el.is_visible():continue
      el.hover();self.check(el)
      page.keyboard.press('Tab');el.focus();self.check(el)
      self.assertNotEqual(el.evaluate('e=>getComputedStyle(e).outlineStyle'),'none')
     self.assertEqual(page.locator('.registration a[href^="tel:"]').count(),0)
     text=page.locator('.registration a[href="sms:+19103955193"]')
     self.assertEqual(text.count(),1)
     self.assertEqual(text.inner_text(),'Text 910-395-5193')
     self.assertEqual(page.locator('.registration a[href^="mailto:"]').count(),1)
     # The live contact card has no form. Verify existing field CSS with a local-only synthetic control.
     page.locator('.registration').evaluate("e=>e.insertAdjacentHTML('beforeend','<div class=field><label for=fixture>Test field</label><input id=fixture placeholder=Example></div>')")
     self.check(page.locator('label[for=fixture]'))
     field=page.locator('#fixture');self.check(field)
     placeholder=field.evaluate("e=>{const p=getComputedStyle(e,'::placeholder');return {color:p.color,opacity:p.opacity}}")
     field.evaluate("(e,c)=>e.style.setProperty('color',c,'important')",placeholder['color']);self.check(field)
     self.assertEqual(placeholder['opacity'],'1')
     self.assertEqual(page.locator('form').count(),0)

if __name__=='__main__':unittest.main()
