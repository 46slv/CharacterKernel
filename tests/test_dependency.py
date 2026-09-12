import unittest

from character_kernel.dependency import DependencyGraph, check_freshness


class DependencyTests(unittest.TestCase):
    def test_freshness_valid(self) -> None:
        report = check_freshness(
            {"body": "shape-v2", "rig_schema": "rig-v1"},
            {"body": "shape-v2", "rig_schema": "rig-v1", "extra": "ignored"},
        )
        self.assertTrue(report.is_fresh)
        self.assertEqual(report.status, "VALID")

    def test_freshness_detects_missing_and_mismatch(self) -> None:
        report = check_freshness(
            {"body": "shape-v2", "rig_schema": "rig-v1"},
            {"body": "shape-v1"},
        )
        self.assertEqual(report.status, "REBIND_REQUIRED")
        self.assertEqual(report.missing, ("rig_schema",))
        self.assertEqual(report.mismatched, ("body",))

    def test_dependency_closure_is_transitive_and_deterministic(self) -> None:
        graph = DependencyGraph(
            {
                "body.parameters": ["body.rest"],
                "body.rest": ["rig.instance", "garment.fit", "hair.roots"],
                "hair.roots": ["hair.generated"],
            }
        )
        self.assertEqual(
            graph.closure(["body.parameters"]),
            ("body.rest", "garment.fit", "hair.generated", "hair.roots", "rig.instance"),
        )


if __name__ == "__main__":
    unittest.main()
