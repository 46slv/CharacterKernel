from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any, Mapping, Sequence

Vec3 = tuple[float, float, float]
_WEIGHT_TOLERANCE = 1e-6
_NORMAL_EPSILON = 1e-12


class AttachmentError(ValueError):
    """Invalid attachment data or unsupported evaluation state."""


class RebindRequired(AttachmentError):
    """Stored correspondence is stale or cannot be safely evaluated."""


@dataclass(frozen=True)
class SurfaceIdentity:
    surface_id: str
    topology_revision: str
    semantic_revision: str | None = None


def _vec3(value: Sequence[float], *, label: str) -> Vec3:
    if len(value) != 3:
        raise AttachmentError(f"{label} must contain exactly 3 values")
    out = tuple(float(v) for v in value)
    if not all(isfinite(v) for v in out):
        raise AttachmentError(f"{label} must contain finite values")
    return out  # type: ignore[return-value]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Vec3, scalar: float) -> Vec3:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(a: Vec3) -> Vec3:
    length = sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    if length <= _NORMAL_EPSILON:
        raise RebindRequired("cannot derive a stable normal from degenerate geometry")
    return (a[0] / length, a[1] / length, a[2] / length)


def _weighted_sum(points: Sequence[Vec3], weights: Sequence[float]) -> Vec3:
    out: Vec3 = (0.0, 0.0, 0.0)
    for point, weight in zip(points, weights, strict=True):
        out = _add(out, _mul(point, weight))
    return out


def _validate_weights(weights: Sequence[float], *, bounded: bool) -> tuple[float, ...]:
    if not weights:
        raise AttachmentError("weights cannot be empty")
    result = tuple(float(w) for w in weights)
    if not all(isfinite(w) for w in result):
        raise AttachmentError("weights must be finite")
    if abs(sum(result) - 1.0) > _WEIGHT_TOLERANCE:
        raise RebindRequired("weights must sum to 1 within tolerance")
    if bounded and any(w < -_WEIGHT_TOLERANCE or w > 1.0 + _WEIGHT_TOLERANCE for w in result):
        raise RebindRequired("barycentric weights are outside the supported triangle")
    return result


@dataclass(frozen=True)
class SurfaceAttachment:
    attachment_id: str
    kind: str
    target_surface_id: str
    target_topology_revision: str
    coordinate_type: str
    indices: tuple[int, ...]
    weights: tuple[float, ...]
    target_semantic_revision: str | None = None
    normal_offset: float = 0.0
    orientation_hint: Vec3 | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise AttachmentError(f"unsupported schema_version={self.schema_version}")
        for label, value in (
            ("attachment_id", self.attachment_id),
            ("kind", self.kind),
            ("target_surface_id", self.target_surface_id),
            ("target_topology_revision", self.target_topology_revision),
        ):
            if not isinstance(value, str) or not value:
                raise AttachmentError(f"{label} must be a non-empty string")
        if self.coordinate_type not in {"BARYCENTRIC_TRIANGLE", "VERTEX_SET"}:
            raise AttachmentError(f"unsupported coordinate_type={self.coordinate_type}")
        if not isfinite(float(self.normal_offset)):
            raise AttachmentError("normal_offset must be finite")
        if self.orientation_hint is not None:
            _vec3(self.orientation_hint, label="orientation_hint")

    def assert_compatible(self, identity: SurfaceIdentity) -> None:
        if identity.surface_id != self.target_surface_id:
            raise RebindRequired(
                f"surface id changed: expected {self.target_surface_id!r}, got {identity.surface_id!r}"
            )
        if identity.topology_revision != self.target_topology_revision:
            raise RebindRequired("target topology revision changed")
        if (
            self.target_semantic_revision is not None
            and identity.semantic_revision != self.target_semantic_revision
        ):
            raise RebindRequired("target semantic revision changed")

    def evaluate(
        self,
        *,
        identity: SurfaceIdentity,
        vertices: Sequence[Sequence[float]],
        triangles: Sequence[Sequence[int]] | None = None,
        vertex_normals: Sequence[Sequence[float]] | None = None,
    ) -> Vec3:
        self.assert_compatible(identity)
        normalized_vertices = tuple(_vec3(v, label="vertex") for v in vertices)

        if self.coordinate_type == "BARYCENTRIC_TRIANGLE":
            return self._evaluate_triangle(
                normalized_vertices,
                triangles=triangles,
                vertex_normals=vertex_normals,
            )
        return self._evaluate_vertex_set(
            normalized_vertices,
            vertex_normals=vertex_normals,
        )

    def _evaluate_triangle(
        self,
        vertices: Sequence[Vec3],
        *,
        triangles: Sequence[Sequence[int]] | None,
        vertex_normals: Sequence[Sequence[float]] | None,
    ) -> Vec3:
        if len(self.indices) != 1:
            raise AttachmentError("triangle attachment requires exactly one triangle id")
        if triangles is None:
            raise RebindRequired("triangle table is unavailable")
        triangle_id = self.indices[0]
        if triangle_id < 0 or triangle_id >= len(triangles):
            raise RebindRequired("triangle id is out of range")

        triangle = tuple(int(i) for i in triangles[triangle_id])
        if len(triangle) != 3:
            raise RebindRequired("triangle table entry does not contain 3 vertex ids")
        if any(i < 0 or i >= len(vertices) for i in triangle):
            raise RebindRequired("triangle references an out-of-range vertex")

        weights = _validate_weights(self.weights, bounded=True)
        if len(weights) != 3:
            raise AttachmentError("triangle attachment requires exactly 3 weights")

        points = [vertices[i] for i in triangle]
        position = _weighted_sum(points, weights)
        if self.normal_offset == 0.0:
            return position

        if vertex_normals is not None:
            normals = self._pick_normals(vertex_normals, triangle)
            normal = _normalize(_weighted_sum(normals, weights))
        else:
            normal = _normalize(_cross(_sub(points[1], points[0]), _sub(points[2], points[0])))
        return _add(position, _mul(normal, float(self.normal_offset)))

    def _evaluate_vertex_set(
        self,
        vertices: Sequence[Vec3],
        *,
        vertex_normals: Sequence[Sequence[float]] | None,
    ) -> Vec3:
        if not self.indices:
            raise AttachmentError("vertex-set attachment requires at least one vertex id")
        if any(i < 0 or i >= len(vertices) for i in self.indices):
            raise RebindRequired("vertex-set attachment references an out-of-range vertex")
        if len(self.indices) != len(self.weights):
            raise AttachmentError("vertex ids and weights must have the same length")

        weights = _validate_weights(self.weights, bounded=False)
        points = [vertices[i] for i in self.indices]
        position = _weighted_sum(points, weights)
        if self.normal_offset == 0.0:
            return position

        if vertex_normals is None:
            raise RebindRequired("vertex normals are required for a vertex-set normal offset")
        normals = self._pick_normals(vertex_normals, self.indices)
        normal = _normalize(_weighted_sum(normals, weights))
        return _add(position, _mul(normal, float(self.normal_offset)))

    @staticmethod
    def _pick_normals(
        vertex_normals: Sequence[Sequence[float]],
        indices: Sequence[int],
    ) -> list[Vec3]:
        if any(i < 0 or i >= len(vertex_normals) for i in indices):
            raise RebindRequired("normal table does not cover the attachment vertices")
        return [_vec3(vertex_normals[i], label="vertex normal") for i in indices]


def attachment_from_dict(data: Mapping[str, Any]) -> SurfaceAttachment:
    coordinate = data.get("coordinate")
    if not isinstance(coordinate, Mapping):
        raise AttachmentError("coordinate must be an object")
    coordinate_type = coordinate.get("type")
    if coordinate_type == "BARYCENTRIC_TRIANGLE":
        indices = (int(coordinate["triangle_id"]),)
    elif coordinate_type == "VERTEX_SET":
        indices = tuple(int(v) for v in coordinate["vertex_ids"])
    else:
        raise AttachmentError(f"unsupported coordinate type: {coordinate_type!r}")

    orientation_raw = data.get("orientation_hint")
    orientation = (
        None if orientation_raw is None else _vec3(orientation_raw, label="orientation_hint")
    )
    return SurfaceAttachment(
        schema_version=int(data.get("schema_version", 1)),
        attachment_id=str(data["attachment_id"]),
        kind=str(data["kind"]),
        target_surface_id=str(data["target_surface_id"]),
        target_topology_revision=str(data["target_topology_revision"]),
        target_semantic_revision=(
            None
            if data.get("target_semantic_revision") is None
            else str(data["target_semantic_revision"])
        ),
        coordinate_type=str(coordinate_type),
        indices=indices,
        weights=tuple(float(w) for w in coordinate["weights"]),
        normal_offset=float(data.get("normal_offset", 0.0)),
        orientation_hint=orientation,
    )
