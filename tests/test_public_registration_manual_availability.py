"""Execute the registration manual renderer without network or payment calls."""
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs/register/index.html").read_text(encoding="utf-8")


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class ManualAvailabilityTests(unittest.TestCase):
    def test_rendered_physical_manual_is_disabled_and_aha_link_remains_available(self):
        renderer = re.search(r"^function productOptions.*$", PAGE, re.MULTILINE).group()
        url = re.search(r"const AHA_BLS_MANUAL_URL=([^;]+);", PAGE).group(1)
        result = subprocess.run(
            ["node", "-e", f"const AHA_BLS_MANUAL_URL={url};const money=n=>'$'+n.toFixed(2);\n{renderer}\nconsole.log(JSON.stringify(productOptions(0,{{courseId:'209806',addons:[{{key:'aha_bls_provider_manual_ebook',unit_amount:1749,active:true}}]}})));"],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        rendered = json.loads(result.stdout)
        parsed = Elements()
        parsed.feed(rendered)
        choices = {attrs["value"]: attrs for tag, attrs in parsed.elements
                   if tag == "input" and "data-manual-choice" in attrs}
        self.assertIn("disabled", choices["physical"])
        self.assertNotIn("checked", choices["physical"])
        self.assertNotIn("disabled", choices["ebook"])
        self.assertIn("checked", choices["own-copy"])
        self.assertIn("Out of stock", rendered)
        self.assertNotIn("Physical BLS Manual — $0", rendered)
        link = next(attrs for tag, attrs in parsed.elements if tag == "a")
        self.assertTrue(link["href"].startswith("https://shopcpr.heart.org/"))
        self.assertEqual(link["target"], "_blank")
        self.assertIn("noopener", link["rel"])

    def test_renewal_prices_come_from_its_catalog_and_missing_products_cannot_be_bought(self):
        renderer = re.search(r"^function productOptions.*$", PAGE, re.MULTILINE).group()
        program = "const AHA_BLS_MANUAL_URL='https://shopcpr.heart.org/';const money=n=>'$'+n.toFixed(2);\n" + renderer
        program += "\nconsole.log(JSON.stringify([productOptions(0,{courseId:'359474',addons:[]}),productOptions(0,{courseId:'359474',addons:[{key:'aha_bls_provider_manual_ebook',unit_amount:2611,active:true}]})]));"
        result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True, encoding="utf-8")
        missing, available = json.loads(result.stdout)
        for rendered, disabled in [(missing, True), (available, False)]:
            parsed = Elements(); parsed.feed(rendered)
            ebook = next(a for tag, a in parsed.elements if tag == "input" and a.get("value") == "ebook")
            self.assertEqual("disabled" in ebook, disabled)
        self.assertIn("$26.11", available)
        self.assertNotIn("$17.49", available)


if __name__ == "__main__":
    unittest.main()
