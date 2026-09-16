import copy
import json
import sys
import unittest
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collect_nse_offer_filings as collector
from publish_transaction import merge_payload
from validate_data import validate_record


class NSEOfferFilingsTests(unittest.TestCase):
    def setUp(self):
        self.raw = (Path(__file__).parent / "fixtures/nse/aaradhya-final-listing.xml").read_bytes()
        self.cells = collector.parse_listing(self.raw)
        self.record = {"id": "aaradhya", "company": "Aaradhya Disposal Industries Limited", "symbol": "AARADHYA",
                       "openDate": "2025-08-04", "closeDate": "2025-08-06", "priceBand": {"min": 110, "max": 116}}
        self.url = "https://nsearchives.nseindia.com/emerge/corporates/content/IPO_LISTING_9019_1506452_08082025013706_WEB.xml"
        self.entry = {"company": self.record["company"], "symbol": "-", "issue_open_date": "04-Aug-2025", "issue_close_date": "06-Aug-2025", "ipo_inlisting_xbrl_link": self.url,
                      "fpDate": "07-Aug-2025", "fpAttach": "https://nsearchives.nseindia.com/emerge/corporates/content/AaradhyaDisposalIndustriesLimited_PROSP.pdf"}

    def test_official_xml_recovers_issue_specific_terms_with_evidence(self):
        changed = collector.merge_terms(self.record, self.entry, self.cells, self.url, "a" * 64)
        self.assertEqual(set(changed), {"lotSize", "listingDate", "listing.issuePrice"})
        self.assertEqual(self.record["lotSize"], 1200)
        self.assertEqual(self.record["marketLot"], 1200)
        self.assertNotIn("minimumBidQuantity", self.record)
        self.assertEqual(self.record["listingDate"], "2025-08-11")
        self.assertEqual(self.record["listing"]["issuePrice"], 116)
        self.assertEqual(self.record["lotSizeEvidence"]["sourceUrl"], self.url)
        self.assertEqual(validate_record(self.record), [])
        self.assertEqual(collector.merge_terms(self.record, self.entry, self.cells, self.url, "a" * 64), [])

    def test_wrong_issuer_security_or_issue_event_is_rejected(self):
        for edits in ({"company": "Another Limited"}, {"symbol": "OTHER"}, {"isin": "INE000000001"}, {"openDate": "2024-08-04"}, {"closeDate": "2025-08-07"}, {"issueEventType": "withdrawal"}):
            row = {**self.record, **edits}
            self.assertEqual(collector.merge_terms(row, self.entry, self.cells, self.url, "hash"), [])
        self.assertFalse(collector.verified_terms({**self.record, "symbol": ""}, self.entry, self.cells))

    def test_register_dates_and_identity_must_agree(self):
        for edits in ({"company": "Another Limited"}, {"issue_open_date": "04-Aug-2024"}, {"issue_close_date": "bad date"}, {"symbol": "OTHER"}):
            self.assertEqual(collector.matched_entries(self.record, [{**self.entry, **edits}]), [])

    def test_later_trading_lots_or_undated_listing_are_rejected(self):
        for edits in ({"DateOfListing": "2025-08-01"}, {"DateOfListing": "2099-01-01"}, {"DateOfIssueOpen": ""}, {"DateOfIssueClose": ""}):
            self.assertFalse(collector.verified_terms(self.record, self.entry, {**self.cells, **edits}))

    def test_existing_application_minimum_and_final_price_are_preserved(self):
        self.record.update(lotSize=2400, minimumBidQuantity=2400, marketLot=1200, listing={"issuePrice": 115}, listingDate="2025-08-12")
        self.assertEqual(collector.merge_terms(self.record, self.entry, self.cells, self.url, "hash"), [])
        self.assertEqual(self.record["lotSize"], 2400)
        self.assertEqual(self.record["listing"]["issuePrice"], 115)

    def test_band_cap_is_not_used_as_a_final_price(self):
        cells = {**self.cells, "FinalIssuePrice": "", "MarketLot": "1200.5"}
        collector.merge_terms(self.record, self.entry, cells, self.url, "hash")
        self.assertNotIn("listing", self.record)
        self.assertNotIn("lotSize", self.record)

    def test_wrong_units_entities_and_conflicting_xml_cells_rejected(self):
        for raw in (self.raw.replace(b'unitRef="shares"', b'unitRef="INR"'), self.raw.replace(b'<xbrli:xbrl ', b'<!DOCTYPE x [<!ENTITY y "bad">]><xbrli:xbrl '), self.raw.replace(b'</xbrli:xbrl>', b'<in-capmkt:MarketLot>999</in-capmkt:MarketLot></xbrli:xbrl>')):
            with self.assertRaises(ValueError):
                collector.parse_listing(raw)

    def test_pdf_discovery_rejects_old_attempts_and_unofficial_links(self):
        self.assertEqual(collector.discover_documents(self.record, [self.entry]), 1)
        self.assertEqual(self.record["documents"][0]["type"], "PROSPECTUS")
        self.assertEqual(collector.discover_documents(self.record, [self.entry]), 0)
        for edits in ({"fpDate": "07-Aug-2024"}, {"fpDate": "05-Aug-2025"}, {"fpAttach": "https://example.com/offer.pdf"}, {"fpAttach": self.url}):
            row = {**self.record, "documents": []}
            self.assertEqual(collector.discover_documents(row, [{**self.entry, **edits}]), 0)

    def test_batched_duplicate_feed_entries_are_idempotent_and_cool_down(self):
        payload = {"ipos": [self.record]}
        def fetch(url, cache=False):
            return self.raw if cache else json.dumps([self.entry, self.entry]).encode()
        with patch.object(collector, "fetch", side_effect=fetch) as mocked:
            report = collector.run(payload)
            self.assertEqual(report["updated"], 1)
            self.assertEqual(sum(call.kwargs.get("cache", False) for call in mocked.call_args_list), 1)
            self.assertEqual(collector.run(payload)["attempted"], 0)

    def test_conflicting_final_filings_are_not_arbitrarily_selected(self):
        alternate = self.url.replace("9019", "9020")
        entries = [self.entry, {**self.entry, "ipo_inlisting_xbrl_link": alternate}]
        def fetch(url, cache=False):
            if not cache:
                return json.dumps(entries).encode()
            return self.raw.replace(b'>1200</in-capmkt:MarketLot>', b'>600</in-capmkt:MarketLot>') if url == alternate else self.raw
        with patch.object(collector, "fetch", side_effect=fetch):
            report = collector.run({"ipos": [self.record]})
        self.assertEqual(report["outcomes"][0]["status"], "conflict")
        self.assertNotIn("lotSize", self.record)

    def test_lot_value_and_evidence_cannot_merge_from_competing_collectors(self):
        base = {"ipos": [copy.deepcopy(self.record)]}
        proposed, current = copy.deepcopy(base), copy.deepcopy(base)
        collector.merge_terms(proposed["ipos"][0], self.entry, self.cells, self.url, "hash")
        current["ipos"][0]["lotSize"] = 2400
        merged, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(merged["ipos"][0]["lotSize"], 2400)
        self.assertNotIn("lotSizeEvidence", merged["ipos"][0])
        self.assertTrue(any(item["path"][-1] == "lotTerms" for item in conflicts))

    def test_validation_detects_stale_evidence(self):
        collector.merge_terms(self.record, self.entry, self.cells, self.url, "hash")
        self.record["lotSize"] = 600
        self.assertTrue(any(item["field"] == "lotSize" for item in validate_record(self.record)))

    def test_completed_record_checkpoints_while_another_download_is_pending(self):
        saved = threading.Event()
        other_url = self.url.replace("9019", "9020")
        other = {**self.record, "id": "other", "company": "Other Industries Limited", "symbol": "OTHER"}
        entries = [self.entry, {**self.entry, "company": other["company"], "ipo_inlisting_xbrl_link": other_url}]
        def fetch(url, cache=False):
            if not cache:
                return json.dumps(entries).encode()
            if url == other_url:
                self.assertTrue(saved.wait(2), "Completed issuer was not checkpointed before the remaining download")
                return self.raw.replace(b">AARADHYA<", b">OTHER<")
            return self.raw
        def checkpoint(payload):
            if payload["ipos"][0].get("lotSize"):
                saved.set()
        with patch.object(collector, "fetch", side_effect=fetch):
            health = collector.run({"ipos": [self.record, other]}, checkpoint=checkpoint)
        self.assertEqual(health["updated"], 2)


if __name__ == "__main__":
    unittest.main()
