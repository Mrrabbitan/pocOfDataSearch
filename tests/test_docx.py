import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.generator import generate_sections  # noqa: E402
from render.docx import render_docx  # noqa: E402


class DocxTests(unittest.TestCase):
    def test_render_docx(self) -> None:
        sample_path = ROOT / "tests" / "fixtures" / "sample_input.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        sections = generate_sections(data, provider=None, prompt_dir=ROOT / "prompts")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.docx"
            render_docx(sections, output_path=output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
