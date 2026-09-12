from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
    examples = sorted((ROOT / "examples").glob("*.json"))
    if not schemas:
        raise SystemExit("no schemas found")
    if not examples:
        raise SystemExit("no examples found")

    for path in schemas + examples:
        load_json(path)

    for path in schemas:
        data = load_json(path)
        if not isinstance(data, dict):
            raise SystemExit(f"{path}: schema root must be an object")
        if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise SystemExit(f"{path}: expected JSON Schema draft 2020-12")
        if data.get("type") != "object":
            raise SystemExit(f"{path}: top-level schema must describe an object")

    print(f"schemas={len(schemas)} examples={len(examples)} status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
