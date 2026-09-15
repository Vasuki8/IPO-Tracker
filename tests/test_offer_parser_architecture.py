import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class OfferParserArchitectureTests(unittest.TestCase):
    def test_numbered_legacy_modules_are_small_aliases(self):
        """Historical import names must never grow back into a parser chain."""
        for version in range(2, 15):
            path = SCRIPTS / f"run_offer_docs_v{version}.py"
            self.assertTrue(path.exists(), path)
            text = path.read_text(encoding="utf-8")
            self.assertLess(len(text.encode("utf-8")), 3500, path)
            tree = ast.parse(text)
            imported_versions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_versions.extend(alias.name for alias in node.names if alias.name.startswith("run_offer_docs_v"))
                elif isinstance(node, ast.ImportFrom) and str(node.module or "").startswith("run_offer_docs_v"):
                    imported_versions.append(str(node.module))
            # v10/v11 temporarily preserve old nested attribute surfaces used by
            # manual callers; no alias may depend on more than one older name.
            self.assertLessEqual(len(imported_versions), 1, (path, imported_versions))
            self.assertIn("legacy_offer_parser", text, path)

    def test_canonical_legacy_parser_does_not_import_numbered_versions(self):
        text = (SCRIPTS / "legacy_offer_parser.py").read_text(encoding="utf-8")
        self.assertNotIn("run_offer_docs_v", text)

    def test_production_critical_fallback_uses_canonical_parser(self):
        text = (SCRIPTS / "run_critical_offer_backfill.py").read_text(encoding="utf-8")
        self.assertIn("import legacy_offer_parser as offer_parser", text)
        self.assertNotIn("run_offer_docs_v", text)


if __name__ == "__main__":
    unittest.main()
