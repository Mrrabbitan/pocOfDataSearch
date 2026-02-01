import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.outline import build_outline  # noqa: E402


class OutlineTests(unittest.TestCase):
    def test_outline_has_sections(self) -> None:
        sample_path = ROOT / "tests" / "fixtures" / "sample_input.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        outline = build_outline(data)
        titles = [item["title"] for item in outline]
        self.assertIn("技术领域", titles)
        self.assertIn("背景技术", titles)
        self.assertIn("发明内容", titles)
        self.assertIn("具体实施方式", titles)


if __name__ == "__main__":
    unittest.main()
