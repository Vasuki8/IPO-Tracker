import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_priority_subscriptions_v2.py"
spec = importlib.util.spec_from_file_location("run_priority_subscriptions_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class PrioritySubscriptionV2Tests(unittest.TestCase):
    def test_current_extensionless_bse_route_is_added(self):
        url = "https://beta.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=7960&status=L"
        variants = mod.official_demand_route_variants(url)
        self.assertIn(
            "https://www.bseindia.com/markets/publicissues/cummdemandschedule?ID=7960&status=L",
            variants,
        )
        self.assertIn(
            "https://beta.bseindia.com/markets/publicissues/cummdemandschedule?ID=7960&status=L",
            variants,
        )
        self.assertIn(url, variants)

    def test_non_demand_url_keeps_normal_official_host_variants(self):
        url = "https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=7960"
        variants = mod.official_demand_route_variants(url)
        self.assertIn(url, variants)
        self.assertIn(
            "https://beta.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=7960",
            variants,
        )


if __name__ == "__main__":
    unittest.main()
