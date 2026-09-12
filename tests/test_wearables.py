import unittest

from character_kernel.attachments import SurfaceAttachment, SurfaceIdentity
from character_kernel.wearables import (
    WearableSelection,
    WearableVariant,
    validate_attachment_batch,
)


class WearableContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = SurfaceIdentity("PANTS", "topology-v1", "semantic-v1")
        self.vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        self.triangles = [(0, 1, 2)]
        self.attachment = SurfaceAttachment(
            attachment_id="belt.A.000",
            kind="GARMENT_FIT",
            target_surface_id="PANTS",
            target_topology_revision="topology-v1",
            target_semantic_revision="semantic-v1",
            coordinate_type="BARYCENTRIC_TRIANGLE",
            indices=(0,),
            weights=(0.2, 0.3, 0.5),
        )

    def test_selection_swaps_without_rewriting_sources(self) -> None:
        source_a = WearableVariant("A", "belt.source.a", "hash-a")
        source_b = WearableVariant("B", "belt.source.b", "hash-b")
        selection = WearableSelection((source_a, source_b), "A")
        swapped = selection.select("B")
        self.assertEqual(swapped.active_variant, "B")
        self.assertEqual(swapped.fit_revision, 1)
        self.assertEqual(swapped.variants, selection.variants)

    def test_unknown_selection_fails_closed(self) -> None:
        selection = WearableSelection((WearableVariant("A", "belt.source.a", "hash-a"),), "A")
        with self.assertRaises(ValueError):
            selection.select("B")

    def test_attachment_batch_reports_valid_and_rebind_required(self) -> None:
        report = validate_attachment_batch(
            [self.attachment],
            identity=self.identity,
            vertices=self.vertices,
            triangles=self.triangles,
        )
        self.assertTrue(report.all_valid)
        stale = validate_attachment_batch(
            [self.attachment],
            identity=SurfaceIdentity("PANTS", "topology-v2", "semantic-v1"),
            vertices=self.vertices,
            triangles=self.triangles,
        )
        self.assertEqual(stale.status, "REBIND_REQUIRED")
        self.assertEqual(stale.invalid_ids, ("belt.A.000",))


if __name__ == "__main__":
    unittest.main()
