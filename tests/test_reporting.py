import unittest

from character_kernel.reporting import canonical_json, semantic_sha256


class ReportingTests(unittest.TestCase):
    def test_hash_is_key_order_independent(self) -> None:
        left = {"b": 2, "a": {"y": 2, "x": 1}}
        right = {"a": {"x": 1, "y": 2}, "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(semantic_sha256(left), semantic_sha256(right))

    def test_hash_changes_when_semantic_payload_changes(self) -> None:
        self.assertNotEqual(
            semantic_sha256({"shape_revision": "v1"}),
            semantic_sha256({"shape_revision": "v2"}),
        )


if __name__ == "__main__":
    unittest.main()
