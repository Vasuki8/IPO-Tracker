import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_price_history import price_rows, index_row, apply_daily
from performance_tracking import apply_quote


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


if __name__ == "__main__":
    unittest.main()
