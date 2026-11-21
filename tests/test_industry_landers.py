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
