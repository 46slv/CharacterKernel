import json
import unittest
from pathlib import Path

from character_kernel.attachments import (
    RebindRequired,
    SurfaceAttachment,
    SurfaceIdentity,
    attachment_from_dict,
)

ROOT = Path(__file__).resolve().parents[1]


class SurfaceAttachmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = SurfaceIdentity(
            surface_id="SCALP_FIT",
            topology_revision="scalp-topology-v1",
            semantic_revision="scalp-semantics-v1",
        )
        self.vertices = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ]
        self.triangles = [(0, 1, 2)]

    def test_example_evaluates_barycentric_position_and_offset(self) -> None:
        data = json.loads((ROOT / "examples" / "surface_attachment.json").read_text())
        attachment = attachment_from_dict(data)
        position = attachment.evaluate(
            identity=self.identity,
            vertices=self.vertices,
            triangles=self.triangles,
        )
        self.assertAlmostEqual(position[0], 0.3)
        self.assertAlmostEqual(position[1], 0.5)
        self.assertAlmostEqual(position[2], 0.002)

    def test_topology_revision_change_fails_closed(self) -> None:
        data = json.loads((ROOT / "examples" / "surface_attachment.json").read_text())
        attachment = attachment_from_dict(data)
        changed = SurfaceIdentity(
            surface_id="SCALP_FIT",
            topology_revision="scalp-topology-v2",
            semantic_revision="scalp-semantics-v1",
        )
        with self.assertRaises(RebindRequired):
            attachment.evaluate(
                identity=changed,
                vertices=self.vertices,
                triangles=self.triangles,
            )

    def test_out_of_range_triangle_fails_closed(self) -> None:
        attachment = SurfaceAttachment(
            attachment_id="x",
            kind="LANDMARK",
            target_surface_id="SCALP_FIT",
            target_topology_revision="scalp-topology-v1",
            target_semantic_revision="scalp-semantics-v1",
            coordinate_type="BARYCENTRIC_TRIANGLE",
            indices=(99,),
            weights=(0.2, 0.3, 0.5),
        )
        with self.assertRaises(RebindRequired):
            attachment.evaluate(
                identity=self.identity,
                vertices=self.vertices,
                triangles=self.triangles,
            )

    def test_invalid_weight_sum_fails_closed(self) -> None:
        attachment = SurfaceAttachment(
            attachment_id="x",
            kind="LANDMARK",
            target_surface_id="SCALP_FIT",
            target_topology_revision="scalp-topology-v1",
            target_semantic_revision="scalp-semantics-v1",
            coordinate_type="BARYCENTRIC_TRIANGLE",
            indices=(0,),
            weights=(0.2, 0.3, 0.4),
        )
        with self.assertRaises(RebindRequired):
            attachment.evaluate(
                identity=self.identity,
                vertices=self.vertices,
                triangles=self.triangles,
            )

    def test_vertex_set_supports_joint_helper_style_aggregation(self) -> None:
        attachment = SurfaceAttachment(
            attachment_id="joint.neck",
            kind="JOINT_SUPPORT",
            target_surface_id="SCALP_FIT",
            target_topology_revision="scalp-topology-v1",
            target_semantic_revision="scalp-semantics-v1",
            coordinate_type="VERTEX_SET",
            indices=(0, 1),
            weights=(0.25, 0.75),
        )
        position = attachment.evaluate(identity=self.identity, vertices=self.vertices)
        self.assertEqual(position, (0.75, 0.0, 0.0))

    def test_vertex_set_offset_requires_normals(self) -> None:
        attachment = SurfaceAttachment(
            attachment_id="x",
            kind="JOINT_SUPPORT",
            target_surface_id="SCALP_FIT",
            target_topology_revision="scalp-topology-v1",
            coordinate_type="VERTEX_SET",
            indices=(0, 1),
            weights=(0.5, 0.5),
            normal_offset=0.1,
        )
        with self.assertRaises(RebindRequired):
            attachment.evaluate(identity=self.identity, vertices=self.vertices)


if __name__ == "__main__":
    unittest.main()
