"""Keep projection releases away from collector/phase mutations."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publication_mode import push_mode

class PublicationModeTests(unittest.TestCase):
    def test_presentation_change_set_uses_bounded_rebuild(self):
        self.assertEqual(push_mode(['scripts/public_quality.py', 'app.js', 'index.html',
            'tests/fixtures/example.json.gz', 'docs/PROJECT_STATUS.md',
            '.github/workflows/frontend.yml', 'data/public_display_holds.json']), 'presentation')

    def test_mixed_or_unknown_source_change_cannot_skip_repair(self):
        for source in ['scripts/final_prospectus_parser.py', 'scripts/phase_status.py',
                       'data/ipos.json', 'data/verified_corrections.json', 'uv.lock',
                       'pyproject.toml', '.github/workflows/unknown.yml']:
            with self.subTest(source=source):
                self.assertEqual(push_mode(['app.js', source]), 'repair')
        self.assertEqual(push_mode([]), 'repair')

    def test_projection_branch_preserves_existing_serialized_publisher(self):
        text = (ROOT/'.github/workflows/refresh.yml').read_text()
        self.assertIn('group: ipo-publication', text)
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        block = text.split('if [[ "$MODE" == "presentation" ]]; then', 1)[1].split('            else', 1)[0]
        self.assertIn('git diff --exit-code -- data/ipos.json', block)
        self.assertIn('git add data/ipos-summary.json ipo/', block)
        for forbidden in ('publish_transaction.py', 'apply_corrections.py', 'run_pipeline.py', 'phase_status.py'):
            self.assertNotIn(forbidden, block)
        self.assertEqual(text.count('contents: write'), 1)
