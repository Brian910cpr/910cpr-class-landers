"""Execute the registration manual renderer without network or payment calls."""
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs/register/index.html").read_text(encoding="utf-8")
RENDERER = "\n".join(re.search(r"^function " + name + r".*$", PAGE, re.MULTILINE).group()
                     for name in ["firstAidOptions", "productOptions"])


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class ManualAvailabilityTests(unittest.TestCase):
    def test_first_aid_recommends_online_with_skills_and_keeps_no_addon_as_default(self):
        program = "const money=n=>'$'+n.toFixed(2);\n" + RENDERER
        program += "\nconsole.log(JSON.stringify(firstAidOptions(0,{addons:[{key:'aha_heartsaver_first_aid_online',unit_amount:5000,active:true},{key:'aha_heartsaver_first_aid_in_person',unit_amount:6000,active:true}]})));"
        result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True, encoding="utf-8")
        rendered = json.loads(result.stdout); parsed = Elements(); parsed.feed(rendered)
        choices = [a for tag, a in parsed.elements if tag == "input" and "data-first-aid-choice" in a]
        self.assertEqual([a["value"] for a in choices], ["online", "in-person", "none"])
        self.assertIn("checked", choices[2])
        self.assertIn("Recommended: online First Aid + in-person skills — $50.00", rendered)
        self.assertIn("First Aid in person — $60.00", rendered)
        self.assertIn("student eBook, and skills testing during your selected class time", rendered)

    def test_rendered_physical_manual_is_disabled_and_aha_link_remains_available(self):
        renderer = RENDERER
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
        renderer = RENDERER
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

    def test_heartcode_has_two_explicit_paths_without_requiring_a_bls_manual(self):
        program = "const money=n=>'$'+n.toFixed(2);\n" + RENDERER
        program += "\nconsole.log(JSON.stringify(productOptions(0,{courseId:'210549',price:55,addons:[{key:'aha_heartcode_bls_online',unit_amount:4100,active:true}]})));"
        result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True, encoding="utf-8")
        rendered = json.loads(result.stdout); parsed = Elements(); parsed.feed(rendered)
        paths = {a["value"]: a for tag, a in parsed.elements if tag == "input" and "data-learning-path" in a}
        self.assertEqual(set(paths), {"skills-only", "online-and-skills"})
        self.assertTrue(all("required" in a for a in paths.values()))
        self.assertIn("$55.00", rendered); self.assertIn("$96.00", rendered)
        self.assertFalse(any("data-manual-choice" in a for tag, a in parsed.elements if tag == "input"))

    def test_other_courses_render_their_configured_options_and_disable_unknown_prices(self):
        escape = re.search(r"^const esc=.*$", PAGE, re.MULTILINE).group()
        program = "const money=n=>'$'+n.toFixed(2);\n" + escape + "\n" + RENDERER
        program += "\nconsole.log(JSON.stringify(productOptions(0,{courseId:'other-course',addons:[{key:'reviewed',display_name:'<unsafe>',unit_amount:1234,active:true},{key:'unknown',unit_amount:0,active:true}]})));"
        result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True, encoding="utf-8")
        rendered = json.loads(result.stdout); parsed = Elements(); parsed.feed(rendered)
        options = {a["data-addon-key"]: a for tag, a in parsed.elements if tag == "input"}
        self.assertNotIn("disabled", options["reviewed"]); self.assertIn("disabled", options["unknown"])
        self.assertIn("$12.34", rendered); self.assertIn("&lt;unsafe&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
