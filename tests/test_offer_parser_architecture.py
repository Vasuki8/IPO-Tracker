import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def imports_with_prefix(path: Path, prefix: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names if alias.name.startswith(prefix))
        elif isinstance(node, ast.ImportFrom) and str(node.module or "").startswith(prefix):
            found.append(str(node.module))
    return found


def numbered_imports(path: Path) -> list[str]:
    return imports_with_prefix(path, "run_offer_docs_v")


class OfferParserArchitectureTests(unittest.TestCase):
    def test_numbered_legacy_modules_are_small_independent_aliases(self):
        """Historical offer-parser import names must never grow back into a chain."""
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

    def test_issuer_offer_runner_uses_current_final_parser_and_no_version_wrappers(self):
        runner = SCRIPTS / "run_issuer_offer_docs.py"
        text = runner.read_text(encoding="utf-8")
        self.assertIn("import final_prospectus_parser as parser", text)
        self.assertIn("import final_prospectus_policy as source_policy", text)
        self.assertNotIn("import legacy_offer_parser as parser", text)
        self.assertIn("from issuer_offer_registry import VALIDATED_OFFER_DOCUMENTS", text)
        self.assertEqual(numbered_imports(runner), [])
        self.assertEqual(imports_with_prefix(runner, "run_issuer_offer_docs_v"), [])
        for version in range(2, 5):
            self.assertFalse((SCRIPTS / f"run_issuer_offer_docs_v{version}.py").exists())

    def test_issuer_registry_is_data_only(self):
        path = SCRIPTS / "issuer_offer_registry.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(imports, [])


if __name__ == "__main__":
    unittest.main()
