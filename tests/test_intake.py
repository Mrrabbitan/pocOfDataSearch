import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.intake import parse_dict, parse_list, normalize_inputs  # noqa: E402


class IntakeTests(unittest.TestCase):
    def test_parse_list(self) -> None:
        value = "模块A；模块B, 模块C"
        self.assertEqual(parse_list(value), ["模块A", "模块B", "模块C"])

    def test_parse_dict(self) -> None:
        value = "术语A=说明A；术语B=说明B"
        self.assertEqual(parse_dict(value), {"术语A": "说明A", "术语B": "说明B"})

    def test_normalize_inputs(self) -> None:
        data = {
            "core_components": "A；B",
            "terms": "术语A=说明A",
        }
        normalized = normalize_inputs(data)
        self.assertEqual(normalized["core_components"], ["A", "B"])
        self.assertEqual(normalized["terms"], {"术语A": "说明A"})


if __name__ == "__main__":
    unittest.main()
