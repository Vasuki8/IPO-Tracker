import importlib.util
import json
import re
import sys
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

    def test_colliding_base_slugs_get_unique_stable_paths(self):
        records = [
            {"id": "A&B", "company": "Alpha Limited", "matchKey": "alpha"},
            {"id": "A B", "company": "Beta Limited", "matchKey": "beta"},
        ]
        assigned = mod.assign_routes(records)
        routes = [route for _, route in assigned]
        self.assertEqual(len(set(routes)), 2)
        self.assertTrue(all(route.startswith("a-b--") for route in routes))
        self.assertTrue(all(row["profilePath"].startswith("ipo/a-b--") for row in records))

    def test_page_embeds_compact_profile_data(self):
        record = {
            "id": "example-limited",
            "company": "Example Limited",
            "symbol": "EXAMPLE",
            "profilePath": "ipo/example-limited/",
            "priceBand": {"min": 100, "max": 110},
            "subscription": {"qib": 2.1, "total": 3.4},
        }
        page = mod.page_html(record, "example-limited")
        self.assertIn('<base href="../../" />', page)
        self.assertIn('data-ipo-id="example-limited"', page)
        self.assertIn('id="ipo-profile-data"', page)
        self.assertIn('company-page.js', page)
        self.assertIn('company.js', page)
        self.assertIn('Example Limited IPO | India IPO Tracker', page)

        match = re.search(
            r'<script id="ipo-profile-data" type="application/json">(.*?)</script>',
            page,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        embedded = json.loads(match.group(1))
        self.assertEqual(embedded["ipo"]["id"], "example-limited")
        self.assertEqual(embedded["ipo"]["subscription"]["total"], 3.4)

    def test_embedded_profile_cannot_close_script_tag(self):
        record = {
            "id": "unsafe",
            "company": "Unsafe </script><script>alert(1)</script> Limited",
            "profilePath": "ipo/unsafe/",
        }
        page = mod.page_html(record, "unsafe")
        match = re.search(
            r'<script id="ipo-profile-data" type="application/json">(.*?)</script>',
            page,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        embedded_text = match.group(1)
        self.assertNotIn("</script>", embedded_text.lower())
        self.assertIn("\\u003c/script>", embedded_text)
        self.assertIn("Unsafe </script>", json.loads(embedded_text)["ipo"]["company"])

    def test_summary_keeps_table_fields_and_drops_heavy_detail_fields(self):
        record = {
            "id": "summary",
            "company": "Summary Limited",
            "symbol": "SUM",
            "profilePath": "ipo/summary/",
            "priceBand": {"min": 95, "max": 100, "internal": "drop"},
            "subscription": {"qib": 2.0, "retail": 3.0, "total": 2.5},
            "subscriptionHistory": [{"capturedAt": "2026-09-15T10:00:00+05:30", "total": 2.5}],
            "listing": {"gainPct": 7.5, "listPrice": 107.5},
            "financials": {"periods": [{"period": "FY26", "revenueCr": 100}]},
            "sources": [{"name": "NSE live", "url": "https://example.test"}, {"name": "SEBI"}],
            "validation": {"status": "verified", "checks": [{"field": "priceBand"}]},
        }
        summary = mod.public_summary_record(record)
        self.assertEqual(summary["subscription"], {"total": 2.5})
        self.assertEqual(summary["listing"], {"gainPct": 7.5})
        self.assertEqual(summary["sourceCount"], 2)
        self.assertEqual(summary["profilePath"], "ipo/summary/")
        self.assertNotIn("subscriptionHistory", summary)
        self.assertNotIn("financials", summary)
        self.assertNotIn("sources", summary)
        self.assertNotIn("checks", summary["validation"])
        self.assertNotIn("internal", summary["priceBand"])

    def test_profile_keeps_display_fields_but_strips_internal_fields(self):
        record = {
            "id": "profile",
            "company": "Profile Limited",
            "profilePath": "ipo/profile/",
            "subscriptionHistory": [
                {
                    "capturedAt": "2026-09-15T10:00:00+05:30",
                    "total": 1.5,
                    "source": "NSE",
                    "rawPayload": {"very": "large"},
                }
            ],
            "documents": [
                {
                    "type": "RHP",
                    "title": "RHP",
                    "url": "https://example.test/rhp.pdf",
                    "filedDate": "2026-09-01",
                    "rawText": "drop this",
                }
            ],
            "sources": [
                {"name": "NSE", "asOf": "2026-09-15T10:00:00+05:30", "url": "https://example.test", "raw": "drop"}
            ],
            "dataAvailability": {"exchange.lotSize": {"status": "source-unavailable"}},
        }
        profile = mod.public_profile_record(record)
        self.assertEqual(profile["subscriptionHistory"][0]["total"], 1.5)
        self.assertNotIn("rawPayload", profile["subscriptionHistory"][0])
        self.assertEqual(profile["documents"][0]["type"], "RHP")
        self.assertNotIn("rawText", profile["documents"][0])
        self.assertNotIn("raw", profile["sources"][0])
        self.assertNotIn("dataAvailability", profile)

    def test_route_digest_ignores_internal_only_changes(self):
        record = {
            "id": "digest",
            "company": "Digest Limited",
            "profilePath": "ipo/digest/",
            "issueSizeCr": 100,
            "dataAvailability": {"internal": "one"},
        }
        first = mod.route_digest(record, "digest")
        record["dataAvailability"] = {"internal": "two"}
        self.assertEqual(first, mod.route_digest(record, "digest"))
        record["issueSizeCr"] = 101
        self.assertNotEqual(first, mod.route_digest(record, "digest"))

    def test_public_summary_payload_is_compact_json_serializable(self):
        payload = {"meta": {"schemaVersion": 7, "generatedAt": "2026-09-15T12:00:00+05:30"}}
        records = [{"id": "a", "company": "A", "profilePath": "ipo/a/"}]
        public = mod.public_summary_payload(payload, records)
        encoded = json.dumps(public, separators=(",", ":"))
        decoded = json.loads(encoded)
        self.assertEqual(decoded["meta"]["publicSummaryVersion"], mod.PUBLIC_SUMMARY_VERSION)
        self.assertEqual(decoded["meta"]["recordCount"], 1)
        self.assertEqual(decoded["ipos"][0]["profilePath"], "ipo/a/")


if __name__ == "__main__":
    unittest.main()
