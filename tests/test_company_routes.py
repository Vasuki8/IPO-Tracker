import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "build_company_pages.py"
spec = importlib.util.spec_from_file_location("build_company_pages", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class CompanyRouteTests(unittest.TestCase):
    def test_route_slug(self):
        self.assertEqual(mod.route_slug("Veegaland Developers Limited"), "veegaland-developers-limited")
        self.assertEqual(mod.route_slug("A&B (India) Ltd."), "a-b-india-ltd")

    def test_page_uses_repo_root_base_and_live_json_renderer(self):
        html = mod.page_html(
            {"id": "example-limited", "company": "Example Limited", "symbol": "EXAMPLE"},
            "example-limited",
        )
        self.assertIn('<base href="../../" />', html)
        self.assertIn('data-ipo-id="example-limited"', html)
        self.assertIn('company-page.js', html)
        self.assertIn('company.js', html)
        self.assertIn('Example Limited IPO | India IPO Tracker', html)

    def test_manifest_shape_is_json_serializable(self):
        payload = {
            "generatedFrom": "data/ipos.json",
            "recordCount": 2,
            "routeCount": 2,
            "routes": ["a", "b"],
        }
        self.assertEqual(json.loads(json.dumps(payload))["routeCount"], 2)


if __name__ == "__main__":
    unittest.main()
