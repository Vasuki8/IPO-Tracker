"""Shared return calculations for final prices, daily reports and quotes."""
import math


def percentage(start, finish):
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in (start, finish)) or start <= 0 or finish < 0:
        return None
    return round((finish / start - 1) * 100, 4)


def refresh_returns(record):
    """Recompute derived values whenever a price or its baseline arrives."""
    listing = record.get("listing") or {}
    if listing:
        listing["gainPct"] = percentage(listing.get("issuePrice"), listing.get("listPrice"))
    performance = record.get("performance")
    if not performance:
        return
    latest = performance.get("latest") or {}
    performance.update(
        issuePrice=listing.get("issuePrice"),
        returnSinceIssuePct=percentage(listing.get("issuePrice"), latest.get("price")),
        returnBasis="Unadjusted price return; excludes dividends and corporate-action adjustments",
        benchmarkExcessReturnPct=None,
    )
    performance.pop("benchmarkReturnBasis", None)
    baseline = performance.get("benchmarkBaseline") or {}
    benchmark = performance.get("benchmarkLatest") or {}
    listed = record.get("listingDate")
    # A dated index close is comparable only with an equity close on that date.
    # Intraday quotes cannot inherit yesterday's close-to-close comparison.
    if (latest.get("priceType") == "official daily close"
            and baseline.get("symbol") == benchmark.get("symbol") == "NIFTY 50"
            and listed and baseline.get("date") == listed
            and benchmark.get("date") == str(latest.get("observedAt", ""))[:10]
            and str(listing.get("asOf", ""))[:10] == listed
            and baseline.get("sourceUrl") and benchmark.get("sourceUrl")
            and listing.get("sourceUrl") and not listing.get("priceConflicts")):
        own = percentage(listing.get("closePrice"), latest.get("price"))
        index = percentage(baseline.get("value"), benchmark.get("value"))
        if own is not None and index is not None:
            performance["benchmarkExcessReturnPct"] = round(own - index, 4)
            performance["benchmarkReturnBasis"] = "Listing-day close to matched-date close; NIFTY 50 price index"
