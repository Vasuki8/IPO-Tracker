import copy
import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_price_history import price_rows, index_row, apply_daily
from performance_tracking import apply_quote
import collect_price_history as collector


class DailyPriceTests(unittest.TestCase):
    def test_csv_dates_series_and_duplicate_symbols_are_checked(self):
        text = "SYMBOL,SERIES,DATE1,OPEN_PRICE,CLOSE_PRICE\nEXAMPLE,EQ,10-Sep-2025,120,125\nOTHER,N1,10-Sep-2025,10,12\nWRONG,EQ,11-Sep-2025,10,12\n"
        self.assertEqual(set(price_rows(text, "2025-09-10")), {"EXAMPLE"})
        self.assertEqual(price_rows(text + "EXAMPLE,BE,10-Sep-2025,130,140\n", "2025-09-10"), {})

    def test_index_identity_date_and_close_are_required(self):
        text = "Index Name,Index Date,Closing Index Value\nNifty 50,10-09-2025,20000\nNifty Bank,10-09-2025,50000\n"
        self.assertEqual(index_row(text, "2025-09-10")["value"], 20000)
        self.assertIsNone(index_row(text, "2025-09-11"))

    def apply(self, record, day, opening, close, index):
        prices = {"EXAMPLE": {"symbol": "EXAMPLE", "date": day, "series": "EQ", "open": opening, "close": close}}
        benchmark = {"symbol": "NIFTY 50", "date": day, "value": index}
        return apply_daily(record, prices, benchmark, day, "https://nsearchives.nseindia.com/prices.csv", "https://nsearchives.nseindia.com/index.csv", "digest")

    def test_listing_open_and_benchmark_use_the_correct_dates_and_baselines(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10", "listing": {"issuePrice": 100}}
        self.apply(record, "2025-09-14", 145, 150, 22000)
        self.assertNotIn("listPrice", record["listing"])
        self.assertIsNone(record["performance"]["benchmarkExcessReturnPct"])
        self.apply(record, "2025-09-10", 120, 125, 20000)
        self.assertEqual(record["listing"]["listPrice"], 120)
        self.assertEqual(record["listing"]["gainPct"], 20)
        self.assertEqual(record["performance"]["returnSinceIssuePct"], 50)
        self.assertEqual(record["performance"]["benchmarkExcessReturnPct"], 10)
        self.assertEqual(record["performance"]["latest"]["observedAt"], "2025-09-14")
        self.assertEqual(record["performance"]["latest"]["timePrecision"], "date")

    def test_previous_listing_and_future_report_are_rejected(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        self.assertFalse(self.apply(record, "2025-09-09", 100, 110, 20000))
        self.assertFalse(self.apply(record, "2099-09-10", 100, 110, 20000))
        self.assertNotIn("performance", record)

    def test_intraday_quote_cannot_replace_same_date_official_close(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        self.apply(record, "2025-09-14", 120, 125, 20000)
        quote = {"info": {"symbol": "EXAMPLE"}, "metadata": {"lastUpdateTime": "14-Sep-2025 12:30:00"}, "priceInfo": {"lastPrice": 122}}
        self.assertFalse(apply_quote(record, quote))
        self.assertEqual(record["performance"]["latest"]["price"], 125)

    def test_daily_close_replaces_same_day_intraday_and_preserves_both(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        quote = {"info": {"symbol": "EXAMPLE"}, "metadata": {"lastUpdateTime": "14-Sep-2025 12:30:00"}, "priceInfo": {"lastPrice": 122}}
        apply_quote(record, quote)
        self.assertTrue(self.apply(record, "2025-09-14", 120, 125, 20000))
        self.assertEqual(record["performance"]["latest"]["price"], 125)
        self.assertEqual(len(record["performance"]["observations"]), 2)
        before = copy.deepcopy(record)
        self.assertFalse(self.apply(record, "2025-09-14", 120, 125, 20000))
        self.assertEqual(record, before)

    def test_backfilled_rows_are_retained_without_regressing_latest(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        self.apply(record, "2025-09-14", 140, 150, 22000)
        self.apply(record, "2025-09-10", 120, 125, 20000)
        self.apply(record, "2025-09-12", 130, 135, 21000)
        self.assertEqual([row["observedAt"] for row in record["performance"]["observations"]], ["2025-09-10", "2025-09-12", "2025-09-14"])
        self.assertEqual(record["performance"]["latest"]["price"], 150)
        self.assertEqual(record["performance"]["benchmarkExcessReturnPct"], 10)

    def test_intraday_quote_clears_close_based_benchmark_comparison(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        self.apply(record, "2025-09-10", 120, 125, 20000)
        quote = {"info": {"symbol": "EXAMPLE"}, "metadata": {"lastUpdateTime": "14-Sep-2025 12:30:00"}, "priceInfo": {"lastPrice": 150}}
        # A date-only index close cannot be matched to an intraday equity quote.
        record["performance"]["benchmarkLatest"] = {"symbol": "NIFTY 50", "date": "2025-09-14", "value": 22000, "sourceUrl": "https://nsearchives.nseindia.com/index.csv"}
        apply_quote(record, quote)
        self.assertIsNone(record["performance"]["benchmarkExcessReturnPct"])
        self.assertNotIn("benchmarkReturnBasis", record["performance"])

    def test_conflicting_listing_prices_keep_original_evidence(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10", "listing": {"listPrice": 119, "sourceUrl": "https://www.nseindia.com/prior"}}
        self.apply(record, "2025-09-10", 120, 125, 20000)
        self.assertEqual(record["listing"]["listPrice"], 119)
        self.assertEqual(record["listing"]["sourceUrl"], "https://www.nseindia.com/prior")
        self.assertEqual(record["listing"]["priceConflicts"][0]["proposed"], 120)
        self.assertIsNone(record["performance"]["benchmarkExcessReturnPct"])

    def test_mismatched_index_cannot_supply_a_baseline(self):
        record = {"symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        prices = {"EXAMPLE": {"symbol": "EXAMPLE", "date": "2025-09-10", "series": "EQ", "open": 120, "close": 125}}
        apply_daily(record, prices, {"symbol": "NIFTY 50", "date": "2025-09-09", "value": 20000}, "2025-09-10", "https://nsearchives.nseindia.com/prices.csv", "https://nsearchives.nseindia.com/index.csv", "hash")
        self.assertNotIn("benchmarkBaseline", record["performance"])

    def test_retry_collects_missing_index_even_after_listing_close_exists(self):
        record = {"id": "example", "symbol": "EXAMPLE", "exchange": "NSE", "listingDate": "2025-09-10", "listing": {"closePrice": 125}}
        calls = []
        def download(session, url):
            calls.append(url)
            if "indices" in url:
                day = "10-09-2025" if "10092025" in url else "14-09-2026"
                return f"Index Name,Index Date,Closing Index Value\nNifty 50,{day},20000\n", "hash"
            day = "10-Sep-2025" if "10092025" in url else "14-Sep-2026"
            return f"SYMBOL,SERIES,DATE1,OPEN_PRICE,CLOSE_PRICE\nEXAMPLE,EQ,{day},120,125\n", "hash"
        with patch.object(collector, "download_csv", side_effect=download), patch.object(collector, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 9, 14, 20, tzinfo=collector.IST)
            collector.run({"ipos": [record]}, 1)
        self.assertTrue(any("ind_close_all_10092025" in url for url in calls))
        self.assertEqual(record["performance"]["benchmarkBaseline"]["date"], "2025-09-10")

    def test_zero_limit_and_future_listings_do_not_fetch_reports(self):
        record = {"id": "future", "symbol": "EXAMPLE", "exchange": "NSE", "listingDate": "2099-09-10"}
        with patch.object(collector, "download_csv") as download:
            self.assertEqual(collector.run({"ipos": [record]}, 30)["selected"], 0)
            record["listingDate"] = "2025-09-10"
            self.assertEqual(collector.run({"ipos": [record]}, 0)["selected"], 0)
            download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
