import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.checks import run_checks  # noqa: E402
from core.generator import generate_sections  # noqa: E402


class CheckTests(unittest.TestCase):
    def test_checks_pass_with_sample(self) -> None:
        sample_path = ROOT / "tests" / "fixtures" / "sample_input.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        sections = generate_sections(data, provider=None, prompt_dir=ROOT / "prompts")
        issues = run_checks(data, sections)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
