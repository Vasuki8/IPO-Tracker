import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def numbered_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names if alias.name.startswith("run_offer_docs_v"))
        elif isinstance(node, ast.ImportFrom) and str(node.module or "").startswith("run_offer_docs_v"):
            found.append(str(node.module))
    return found


class OfferParserArchitectureTests(unittest.TestCase):
    def test_numbered_legacy_modules_are_small_independent_aliases(self):
        """Historical import names must never grow back into a parser chain."""
        for version in range(2, 15):
            path = SCRIPTS / f"run_offer_docs_v{version}.py"
            self.assertTrue(path.exists(), path)
            text = path.read_text(encoding="utf-8")
            self.assertLess(len(text.encode("utf-8")), 3500, path)
            self.assertEqual(numbered_imports(path), [], path)
            self.assertIn("legacy_offer_parser", text, path)

    def test_canonical_legacy_parser_has_no_numbered_imports(self):
        path = SCRIPTS / "legacy_offer_parser.py"
        self.assertEqual(numbered_imports(path), [])

    def test_production_critical_fallback_uses_canonical_parser(self):
        path = SCRIPTS / "run_critical_offer_backfill.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("import legacy_offer_parser as offer_parser", text)
        self.assertEqual(numbered_imports(path), [])


if __name__ == "__main__":
    unittest.main()
