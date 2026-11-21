from html.parser import HTMLParser
import json
import unittest
from urllib.parse import urlsplit
from xml.etree import ElementTree

from scripts.build_industry_landers import BASE, CTA, DIRECTORY, DOCS, load, output_set, sitemap_paths

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
    def get(self, tag, **attrs):
        return [a for t,a in self.tags if t==tag and all(a.get(k)==v for k,v in attrs.items())]

class IndustryLandersTest(unittest.TestCase):
    def test_outputs_match_and_are_unique(self):
        outputs=list(output_set())
        self.assertEqual(len(outputs),len(set(p for p,_ in outputs)))
        for p, body in outputs:
            self.assertEqual(body,p.read_text())
        titles=[]
        descriptions=[]
        for slug in sitemap_paths():
            body=(DOCS/slug.strip("/")/"index.html").read_text()
            page=Page(body)
            self.assertEqual(1,len(page.get("h1")))
            self.assertIn(BASE+slug,[a["href"] for a in page.get("link",rel="canonical")])
            self.assertEqual("index,follow",page.get("meta",name="robots")[0]["content"])
            self.assertEqual(1,body.count("<!-- Google Tag Manager -->"))
            self.assertEqual(1,body.count("<!-- Google Tag Manager (noscript) -->"))
            self.assertEqual(1,len(page.get("script",type="application/ld+json")))
            schema=json.loads(body.split('application/ld+json">',1)[1].split("</script>",1)[0])
            self.assertEqual("https://schema.org",schema["@context"])
            self.assertNotIn("enrollware",body.lower())
            self.assertNotIn("/register/",body.lower())
            self.assertIn(CTA,[a.get("href") for a in page.get("a")])
            descriptions.append(page.get("meta",name="description")[0]["content"])
            titles.append(body.split("<title>",1)[1].split("</title>",1)[0])
            if slug != DIRECTORY:
                self.assertIn(">Course family<",body)
                self.assertIn(">Course type<",body)
                self.assertIn(">Who to train<",body)
                self.assertIn(">What do the authorities say?<",body)
                self.assertIn(">Which certification does your team need?<",body)
                self.assertEqual(1,len(page.get("img",src="/assets/industry-landers/authority-glasses.webp",loading="lazy",alt="")))
                self.assertNotIn("planning training for a group or workplace",body)
                self.assertNotIn("confirm instructor availability, travel",body)
                self.assertNotIn("Bring a floor plan",body)
                self.assertIn("Tell us how many people need training",body)
                self.assertIn("<li><strong>Fully in person</strong> is our usual recommendation",body)
                self.assertRegex(body, r"<li><strong>Blended[,:]")
                self.assertIn("more economical",body)
                if slug.endswith("/merchant-mariners/"):
                    self.assertNotIn("groups of four",body)
                    self.assertIn("approved delivery conditions",body)
                else:
                    self.assertIn("on their own schedule",body)
                    self.assertIn("in pairs or groups of four",body)
                    self.assertIn("quote either format or both",body)
                self.assertIn("replace the preset Program",body)
                self.assertIn('<div class="actions hero-actions">',body)
                self.assertEqual(
                    [CTA, "mailto:info@910cpr.com", "tel:+19103955193"],
                    [a["href"] for a in page.get("a") if a.get("class") in {"btn primary", "btn secondary"}],
                )
                self.assertTrue(any(a.get("src","").startswith("/images/0") for a in page.get("img")))
        self.assertEqual(len(titles),len(set(titles)))
        self.assertEqual(len(descriptions),len(set(descriptions)))

    def test_sitemap_and_navigation(self):
        idx=(DOCS/DIRECTORY.strip("/")/"index.html").read_text()
        public_hub=(DOCS/"group-training.html").read_text()
        self.assertIn(f'href="{DIRECTORY}"',public_hub)
        self.assertIn('id="request-form"',public_hub)
        root=ElementTree.parse(DOCS/"sitemap.xml").getroot()
        current=[n.text for n in root.findall("{*}url/{*}loc")]
        for url in sitemap_paths():
            self.assertEqual(1,current.count(BASE+url))
            if url!=DIRECTORY: self.assertIn(f'href="{url}"',idx)

    def test_authority_answers_on_page_with_quiet_source_links(self):
        conf=load()
        sources=conf["sources"]
        for row in conf["industries"]:
            slug=row[0]
            evidence=conf["authority_evidence"][slug]
            page=(DOCS/"group-training"/slug/"index.html").read_text()
            authority=page.split('<section class="card authority">',1)[1].split("</section>",1)[0]
            self.assertIn("authority-from",authority)
            self.assertIn("authority-references",authority)
            self.assertNotIn("regulatory-and-approvals-compliance",authority)
            self.assertNotIn("<iframe",authority)
            self.assertNotIn('class="btn',authority)
            self.assertTrue(authority.index("authority-from") < authority.index("authority-references"))
            links=Page(authority).get("a")
            self.assertEqual([sources[key][1] for key in evidence["sources"]], [a["href"] for a in links])
            self.assertTrue(all(a.get("target")=="_blank" and a.get("rel")=="noopener noreferrer" for a in links))
            self.assertLessEqual(len(evidence["excerpt"].split()),25)
            if evidence["excerpt"]:
                self.assertIn("Short official excerpt",authority)
            else:
                self.assertIn("Plain-English summary above",authority)
        workplace=(DOCS/"group-training/workplaces/index.html").read_text()
        self.assertIn("29 CFR 1910.151(b)",workplace)
        self.assertIn("a person or persons shall be adequately trained to render first aid.",workplace)
        self.assertIn("used to treat all injured employees",workplace)

    def test_issuer_options_are_disclosed_without_javascript(self):
        for row in load()["industries"]:
            slug=row[0]
            page=(DOCS/"group-training"/slug/"index.html").read_text()
            brands=page.split('<section class="card brands">',1)[1].split("</section>",1)[0]
            parsed=Page(brands)
            self.assertEqual([a["class"] for a in parsed.get("li")], ["brand-aha", "brand-hsi", "brand-arc"])
            self.assertEqual(3,len(parsed.get("details")))
            self.assertEqual(3,len(parsed.get("summary")))
            self.assertEqual(3,len(parsed.get("p",**{"class":"issuer-hover","aria-hidden":"true"})))
            self.assertNotIn("<script",brands)
            if slug=="merchant-mariners":
                self.assertIn("HSINST-203",brands)
                self.assertIn("do not present a separate Red Cross option",brands)
                self.assertIn("does not satisfy STCW endorsements",brands)
        css=(DOCS/"assets/industry-landers/industry.css").read_text()
        self.assertIn(".brand-picker li:hover .issuer-hover{display:block}",css)
        self.assertIn(".brand-picker .brand-aha{grid-row:1;grid-column:2/4}",css)
        self.assertIn(".brand-picker .brand-hsi{grid-row:2;grid-column:2}",css)
        self.assertIn(".brand-picker .brand-arc{grid-row:2;grid-column:3}",css)

    def test_sources_and_local_assets(self):
        conf=load()
        for row in conf["industries"]:
            for key in row[-2].split(","):
                link=conf["sources"][key][1]
                self.assertEqual("https",urlsplit(link).scheme)
                self.assertNotIn("osmanager",link)
            page=Page((DOCS/"group-training"/row[0]/"index.html").read_text())
            for attr, key in [(x,"src") for x in page.get("img")]+[(x,"srcset") for x in page.get("source")]:
                src=attr[key]
                self.assertTrue((DOCS/src.strip("/")).is_file(),src)

if __name__=="__main__": unittest.main()
