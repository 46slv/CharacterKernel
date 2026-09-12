import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContractFileTests(unittest.TestCase):
    def test_json_files_parse(self) -> None:
        paths = list((ROOT / "schemas").glob("*.schema.json"))
        paths += list((ROOT / "examples").glob("*.json"))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_schemas_pin_draft_2020_12(self) -> None:
        for path in (ROOT / "schemas").glob("*.schema.json"):
            with self.subTest(path=path):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    data.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )


if __name__ == "__main__":
    unittest.main()
