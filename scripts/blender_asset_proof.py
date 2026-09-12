"""Deterministic Blender proof for the public wearable attachment contract.

The script is both the redistribution-safe fixture builder and the narrow
Blender adapter.  It keeps source meshes separate from fitted results and
uses character_kernel.SurfaceAttachment for every persisted correspondence.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector, geometry

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from character_kernel.attachments import SurfaceAttachment, SurfaceIdentity, attachment_from_dict
from character_kernel.dependency import DependencyGraph
from character_kernel.reporting import canonical_json, semantic_sha256
from character_kernel.wearables import WearableSelection, WearableVariant, validate_attachment_batch


CONTRACT = "CHARACTERKERNEL_SYNTHETIC_WEARABLE_V1"
FIXTURE_ID = "synthetic_body_pants_belt_v1"
MANIFEST_PROP = "character_kernel_wearable_manifest"
COLLECTION_NAME = "CharacterKernel"
BODY_NAME = "CK_Body_Source"
PANTS_SOURCE_NAME = "CK_Pants_Source"
PANTS_FITTED_NAME = "CK_Pants_Fitted"
BELT_SOURCE_NAMES = {"A": "CK_Belt_Source_A", "B": "CK_Belt_Source_B"}
BELT_RESULT_NAME = "CK_Belt_Result"
BODY_WIDTH_PLUS = "CK_pants_width_plus"
BODY_WIDTH_MINUS = "CK_pants_width_minus"
BODY_WIDTH_SPAN = 0.10
BODY_SEGMENTS = 16


def _args() -> dict[str, str]:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = {"mode": "roundtrip", "out": str(ROOT / "evidence" / "local" / "blender_asset_port")}
    index = 0
    while index < len(raw):
        token = raw[index]
        if token.startswith("--") and index + 1 < len(raw) and not raw[index + 1].startswith("--"):
            args[token[2:].replace("-", "_")] = raw[index + 1]
            index += 2
        else:
            index += 1
    return args


def _candidate_revision() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"
    return result.stdout.strip() or "UNAVAILABLE"


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _vector_rows(values) -> list[list[float]]:
    return [[round(float(value.x), 9), round(float(value.y), 9), round(float(value.z), 9)] for value in values]


def _mesh_vertices(mesh) -> tuple[tuple[float, float, float], ...]:
    return tuple((float(vertex.co.x), float(vertex.co.y), float(vertex.co.z)) for vertex in mesh.vertices)


def _rest_shape_hash(values) -> str:
    rows = []
    for value in values:
        if hasattr(value, "co"):
            value = value.co
        rows.append([round(float(component), 9) for component in value])
    return semantic_sha256(rows)


def _topology_hash(mesh) -> str:
    return semantic_sha256(
        {
            "vertex_count": len(mesh.vertices),
            "polygons": [list(map(int, polygon.vertices)) for polygon in mesh.polygons],
        }
    )


def _uv_hash(mesh) -> str | None:
    layer = mesh.uv_layers.active
    if layer is None:
        return None
    return semantic_sha256(
        [[round(float(value), 9) for value in layer.data[index].uv] for index in range(len(layer.data))]
    )


def _material(name: str, color: tuple[float, float, float], *, metallic: float = 0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.metallic = metallic
    material.roughness = 0.42
    if material.use_nodes:
        shader = material.node_tree.nodes.get("Principled BSDF")
        if shader is not None:
            shader.inputs["Base Color"].default_value = (*color, 1.0)
            shader.inputs["Metallic"].default_value = metallic
            shader.inputs["Roughness"].default_value = 0.42
    return material


def _mesh(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    materials,
    material_indices: list[int] | None = None,
):
    old = bpy.data.meshes.get(name)
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    if material_indices is not None:
        for polygon, material_index in zip(mesh.polygons, material_indices, strict=True):
            polygon.material_index = int(material_index)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    polygon_count = max(1, len(mesh.polygons))
    for polygon in mesh.polygons:
        for loop_offset, loop_index in enumerate(polygon.loop_indices):
            uv_layer.data[loop_index].uv = (
                round(float(polygon.index) / polygon_count, 9),
                round(float(loop_offset) / max(1, len(polygon.vertices)), 9),
            )
    return mesh


def _collection():
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _remove_object(name: str) -> None:
    old = bpy.data.objects.get(name)
    if old is None:
        return
    old_mesh = old.data if old.type == "MESH" else None
    bpy.data.objects.remove(old, do_unlink=True)
    if old_mesh is not None and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)


def _new_object(name: str, mesh, *, visible: bool):
    _remove_object(name)
    obj = bpy.data.objects.new(name, mesh)
    _collection().objects.link(obj)
    obj.hide_render = not visible
    return obj


def _ring(vertices, *, z: float, rx: float, ry: float, count: int = BODY_SEGMENTS) -> list[int]:
    start = len(vertices)
    for index in range(count):
        angle = 2.0 * math.pi * index / count
        vertices.append((rx * math.cos(angle), ry * math.sin(angle), z))
    return list(range(start, start + count))


def _join_rings(faces, lower: list[int], upper: list[int]) -> list[int]:
    ids = []
    for index, current in enumerate(lower):
        nxt = lower[(index + 1) % len(lower)]
        upper_nxt = upper[(index + 1) % len(upper)]
        faces.append((current, nxt, upper_nxt, upper[index]))
        ids.append(len(faces) - 1)
    return ids


def _body_geometry():
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    rings = [
        _ring(vertices, z=0.0, rx=0.42, ry=0.30),
        _ring(vertices, z=0.65, rx=0.46, ry=0.32),
        _ring(vertices, z=1.15, rx=0.50, ry=0.34),
        _ring(vertices, z=1.75, rx=0.38, ry=0.27),
    ]
    side_faces: list[int] = []
    for lower, upper in zip(rings, rings[1:]):
        side_faces.extend(_join_rings(faces, lower, upper))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))
    regions = {
        "body.region.lower": side_faces[: BODY_SEGMENTS * 3],
        "body.region.waist": side_faces[BODY_SEGMENTS * 2 : BODY_SEGMENTS * 3],
    }
    return vertices, faces, regions, list(range(BODY_SEGMENTS * 3))


def _pants_geometry():
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    lower = _ring(vertices, z=0.12, rx=0.50, ry=0.37)
    upper = _ring(vertices, z=1.18, rx=0.55, ry=0.40)
    waistband_faces = _join_rings(faces, lower, upper)
    faces.append(tuple(reversed(lower)))
    faces.append(tuple(upper))
    return vertices, faces, waistband_faces


def _belt_geometry(variant: str):
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    if variant == "A":
        z_lower, z_upper, rx, ry, buckle_half = 1.11, 1.19, 0.60, 0.44, 0.07
    else:
        z_lower, z_upper, rx, ry, buckle_half = 1.05, 1.25, 0.64, 0.47, 0.095
    lower = _ring(vertices, z=z_lower, rx=rx, ry=ry)
    upper = _ring(vertices, z=z_upper, rx=rx, ry=ry)
    material_indices = _join_rings(faces, lower, upper)
    base = len(vertices)
    vertices.extend(
        [
            (-buckle_half, -ry - 0.025, z_lower + 0.005),
            (buckle_half, -ry - 0.025, z_lower + 0.005),
            (buckle_half, -ry - 0.025, z_upper - 0.005),
            (-buckle_half, -ry - 0.025, z_upper - 0.005),
        ]
    )
    faces.append((base, base + 1, base + 2, base + 3))
    material_indices.append(1)
    return vertices, faces, material_indices


def _triangle_table(mesh, coordinates):
    table = []
    for face_id, polygon in enumerate(mesh.polygons):
        ids = tuple(int(index) for index in polygon.vertices)
        for triangle_index in range(1, len(ids) - 1):
            triangle = (ids[0], ids[triangle_index], ids[triangle_index + 1])
            table.append(
                {
                    "face_id": face_id,
                    "triangle_index": triangle_index - 1,
                    "vertices": triangle,
                    "coords": tuple(Vector(coordinates[index]) for index in triangle),
                }
            )
    return table


def _barycentric(point: Vector, a: Vector, b: Vector, c: Vector) -> tuple[float, float, float]:
    v0, v1, v2 = b - a, c - a, point - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    denominator = d00 * d11 - d01 * d01
    if abs(denominator) < 1e-12:
        raise ValueError("degenerate attachment triangle")
    weight_b = (d11 * d20 - d01 * d21) / denominator
    weight_c = (d00 * d21 - d01 * d20) / denominator
    return (1.0 - weight_b - weight_c, weight_b, weight_c)


def _bind(
    points,
    target,
    *,
    target_surface_id: str,
    target_semantic_revision: str | None,
    candidate_faces: set[int],
    normal_offset: float,
    attachment_prefix: str,
):
    coordinates = _evaluated_vertices(target)
    table = _triangle_table(target.data, coordinates)
    candidates = [entry for entry in table if entry["face_id"] in candidate_faces]
    if not candidates:
        raise RuntimeError("no candidate surface faces for attachment")
    topology_revision = _topology_hash(target.data)
    records = []
    for index, point_value in enumerate(points):
        point = Vector(point_value)
        best = None
        for entry in candidates:
            a, b, c = entry["coords"]
            closest = geometry.closest_point_on_tri(point, a, b, c)
            distance = (closest - point).length
            key = (round(float(distance), 12), int(entry["face_id"]), int(entry["triangle_index"]))
            if best is None or key < best[0]:
                best = (key, entry, closest)
        _, entry, closest = best
        a, b, c = entry["coords"]
        normal = (b - a).cross(c - a)
        if normal.length < 1e-12:
            raise RuntimeError("degenerate target triangle")
        normal.normalize()
        records.append(
            SurfaceAttachment(
                attachment_id=f"{attachment_prefix}.{index:03d}",
                kind="GARMENT_FIT",
                target_surface_id=target_surface_id,
                target_topology_revision=topology_revision,
                target_semantic_revision=target_semantic_revision,
                coordinate_type="BARYCENTRIC_TRIANGLE",
                indices=(next(i for i, candidate in enumerate(table) if candidate is entry),),
                weights=tuple(round(float(weight), 9) for weight in _barycentric(closest, a, b, c)),
                normal_offset=float(normal_offset),
                orientation_hint=tuple(float(value) for value in normal),
            )
        )
    return tuple(records)


def _attachment_dict(attachment: SurfaceAttachment) -> dict:
    if attachment.coordinate_type == "BARYCENTRIC_TRIANGLE":
        coordinate = {
            "type": "BARYCENTRIC_TRIANGLE",
            "triangle_id": int(attachment.indices[0]),
            "weights": list(attachment.weights),
        }
    else:
        coordinate = {
            "type": "VERTEX_SET",
            "vertex_ids": list(attachment.indices),
            "weights": list(attachment.weights),
        }
    return {
        "schema_version": attachment.schema_version,
        "attachment_id": attachment.attachment_id,
        "kind": attachment.kind,
        "target_surface_id": attachment.target_surface_id,
        "target_topology_revision": attachment.target_topology_revision,
        "target_semantic_revision": attachment.target_semantic_revision,
        "space": "TARGET_LOCAL",
        "unit_scale_meters": 1.0,
        "coordinate": coordinate,
        "normal_offset": attachment.normal_offset,
        "orientation_hint": None if attachment.orientation_hint is None else list(attachment.orientation_hint),
    }


def _attachments(values):
    return tuple(attachment_from_dict(value) if isinstance(value, dict) else value for value in values)


def _evaluated_vertices(obj) -> tuple[tuple[float, float, float], ...]:
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return _mesh_vertices(mesh)
    finally:
        evaluated.to_mesh_clear()


def _set_vertices(obj, coordinates) -> None:
    if len(obj.data.vertices) != len(coordinates):
        raise RuntimeError(f"vertex count changed for {obj.name}")
    for vertex, coordinate in zip(obj.data.vertices, coordinates, strict=True):
        vertex.co = coordinate
    obj.data.update()


def _copy_object(source, name: str, *, visible: bool):
    obj = _new_object(name, source.data.copy(), visible=visible)
    obj.location = source.location
    return obj


def _source_signature(obj) -> dict:
    shape_keys = obj.data.shape_keys
    return {
        "topology_hash": _topology_hash(obj.data),
        "rest_shape_hash": _rest_shape_hash(_mesh_vertices(obj.data)),
        "uv_hash": _uv_hash(obj.data),
        "materials": [material.name for material in obj.data.materials],
        "shape_key_names": [] if shape_keys is None else [block.name for block in shape_keys.key_blocks],
    }


def _body_semantic(body) -> tuple[dict, str]:
    regions = json.loads(body["semantic_regions"])
    payload = {
        "surface_id": "body.surface.synthetic",
        "derivation": body["semantic_derivation"],
        "regions": regions,
    }
    return payload, semantic_sha256(payload)


def _pants_semantic(pants) -> tuple[dict, str]:
    regions = json.loads(pants["semantic_regions"])
    payload = {
        "surface_id": "pants.surface.synthetic",
        "derivation": pants["semantic_derivation"],
        "regions": regions,
    }
    return payload, semantic_sha256(payload)


def _identity(target, *, surface_id: str | None = None, semantic_revision: str | None = None) -> SurfaceIdentity:
    return SurfaceIdentity(
        surface_id=surface_id or str(target.get("surface_id", target.name)),
        topology_revision=_topology_hash(target.data),
        semantic_revision=semantic_revision or str(target.get("semantic_map_hash", "")) or None,
    )


def _attachment_report(records, target, *, surface_id: str, semantic_revision: str | None):
    coordinates = _evaluated_vertices(target)
    table = _triangle_table(target.data, coordinates)
    triangles = [entry["vertices"] for entry in table]
    report = validate_attachment_batch(
        _attachments(records),
        identity=_identity(target, surface_id=surface_id, semantic_revision=semantic_revision),
        vertices=coordinates,
        triangles=triangles,
    )
    return {
        "status": report.status,
        "total": report.total,
        "valid": report.valid,
        "invalid_ids": list(report.invalid_ids),
        "all_valid": report.all_valid,
    }


def _evaluate_records(records, target, *, surface_id: str, semantic_revision: str | None):
    values = _attachments(records)
    coordinates = _evaluated_vertices(target)
    table = _triangle_table(target.data, coordinates)
    triangles = [entry["vertices"] for entry in table]
    identity = _identity(target, surface_id=surface_id, semantic_revision=semantic_revision)
    return tuple(
        attachment.evaluate(identity=identity, vertices=coordinates, triangles=triangles)
        for attachment in values
    )


def _store_manifest(manifest: dict) -> None:
    bpy.context.scene[MANIFEST_PROP] = canonical_json(manifest)


def _load_manifest() -> dict:
    raw = bpy.context.scene.get(MANIFEST_PROP)
    if not raw:
        raise RuntimeError("CharacterKernel wearable manifest is missing")
    return json.loads(raw)


def _save(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), check_existing=False)
    return str(path)


def _ensure_body_keys(body, lower_vertex_ids: list[int]) -> None:
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis", from_mix=False)
    for name, sign in ((BODY_WIDTH_PLUS, 1.0), (BODY_WIDTH_MINUS, -1.0)):
        block = body.data.shape_keys.key_blocks.get(name)
        if block is None:
            block = body.shape_key_add(name=name, from_mix=False)
            for index in lower_vertex_ids:
                basis = body.data.vertices[index].co
                block.data[index].co = (basis.x, basis.y * (1.0 + sign * BODY_WIDTH_SPAN), basis.z)


def _set_width(body, value: float) -> float:
    value = max(0.90, min(1.10, float(value)))
    keys = body.data.shape_keys
    if keys is None:
        raise RuntimeError("body width shape keys are missing")
    plus = keys.key_blocks.get(BODY_WIDTH_PLUS)
    minus = keys.key_blocks.get(BODY_WIDTH_MINUS)
    if plus is None or minus is None:
        raise RuntimeError("body width shape keys are missing")
    delta = value - 1.0
    plus.value = max(0.0, delta / BODY_WIDTH_SPAN)
    minus.value = max(0.0, -delta / BODY_WIDTH_SPAN)
    bpy.context.view_layer.update()
    return round(value, 6)


def _width(body) -> float:
    keys = body.data.shape_keys
    if keys is None:
        return 1.0
    plus = keys.key_blocks.get(BODY_WIDTH_PLUS)
    minus = keys.key_blocks.get(BODY_WIDTH_MINUS)
    if plus is None or minus is None:
        return 1.0
    return round(1.0 + BODY_WIDTH_SPAN * (plus.value - minus.value), 6)


def _body_state(body) -> dict:
    semantic, semantic_hash = _body_semantic(body)
    return {
        "topology_hash": _topology_hash(body.data),
        "semantic": semantic,
        "semantic_map_hash": semantic_hash,
        "uv_hash": _uv_hash(body.data),
        "rest_shape_hash": _rest_shape_hash(_evaluated_vertices(body)),
        "source_rest_shape_hash": _rest_shape_hash(_mesh_vertices(body.data)),
        "parameters": {"pants_width": _width(body)},
    }


def _dependency_closure() -> tuple[str, ...]:
    return DependencyGraph(
        {
            "body.param.pants_width": ["body.evaluated_rest"],
            "body.evaluated_rest": ["pants.fitted"],
            "pants.fitted": ["belt.result"],
        }
    ).closure(["body.param.pants_width"])


def _core_is_bpy_free() -> bool:
    source_root = ROOT / "src" / "character_kernel"
    return not any(
        token in path.read_text(encoding="utf-8")
        for path in source_root.glob("*.py")
        for token in ("import bpy", "from bpy")
    )


def _create_scene() -> tuple[object, object, dict[str, object]]:
    body_vertices, body_faces, body_regions, lower_ids = _body_geometry()
    body = _new_object(
        BODY_NAME,
        _mesh("CK_Body_Source_Mesh", body_vertices, body_faces, [_material("CK_Body_Matte", (0.32, 0.38, 0.48))]),
        visible=True,
    )
    body["source_kind"] = "authoring"
    body["source_id"] = "body.synthetic.source"
    body["surface_id"] = "body.surface.synthetic"
    body["semantic_derivation"] = "synthetic.body.regions.v1"
    body["semantic_regions"] = json.dumps(body_regions, sort_keys=True, separators=(",", ":"))
    body["topology_hash"] = _topology_hash(body.data)
    body["uv_hash"] = _uv_hash(body.data) or "UNAVAILABLE"
    _ensure_body_keys(body, lower_ids)
    _set_width(body, 1.0)

    pants_vertices, pants_faces, waistband_faces = _pants_geometry()
    pants = _new_object(
        PANTS_SOURCE_NAME,
        _mesh("CK_Pants_Source_Mesh", pants_vertices, pants_faces, [_material("CK_Pants_Matte", (0.06, 0.08, 0.12))]),
        visible=False,
    )
    pants["source_kind"] = "authoring"
    pants["source_id"] = "pants.synthetic.source"
    pants["surface_id"] = "pants.surface.synthetic"
    pants["semantic_derivation"] = "synthetic.pants.regions.v1"
    pants["semantic_regions"] = json.dumps({"pants.region.waistband": waistband_faces}, separators=(",", ":"))
    pants["waistband_face_ids"] = json.dumps(waistband_faces, separators=(",", ":"))

    belts: dict[str, object] = {}
    belt_materials = {
        "A": (_material("CK_Belt_A", (0.82, 0.86, 0.94)), "belt.synthetic.a"),
        "B": (_material("CK_Belt_B", (0.18, 0.23, 0.31)), "belt.synthetic.b"),
    }
    buckle = _material("CK_Buckle_Metal", (0.55, 0.62, 0.72), metallic=0.72)
    for variant in ("A", "B"):
        vertices, faces, indices = _belt_geometry(variant)
        ring, source_id = belt_materials[variant]
        belt = _new_object(
            BELT_SOURCE_NAMES[variant],
            _mesh(f"CK_Belt_Source_{variant}_Mesh", vertices, faces, [ring, buckle], indices),
            visible=False,
        )
        belt["source_kind"] = "authoring"
        belt["source_id"] = source_id
        belt["variant"] = variant
        belt["surface_id"] = f"belt.surface.synthetic.{variant.lower()}"
        belts[variant] = belt
    return body, pants, belts


def _asset_manifest(
    body,
    pants,
    belts: dict[str, object],
    body_state: dict,
    pants_semantic: dict,
    pants_semantic_hash: str,
    pants_records: tuple[SurfaceAttachment, ...],
    belt_records: dict[str, tuple[SurfaceAttachment, ...]],
    pants_fit_hash: str,
    belt_a_hash: str,
) -> dict:
    variants = tuple(
        WearableVariant(variant, str(belts[variant]["source_id"]), semantic_sha256(_source_signature(belts[variant])))
        for variant in ("A", "B")
    )
    selection = WearableSelection(variants, "A")
    source_signatures = {
        "body": _source_signature(body),
        "pants": _source_signature(pants),
        "belt_A": _source_signature(belts["A"]),
        "belt_B": _source_signature(belts["B"]),
    }
    return {
        "contract": CONTRACT,
        "schema_version": 1,
        "candidate_revision": _candidate_revision(),
        "fixture": {"id": FIXTURE_ID, "builder_sha256": _sha256_file(Path(__file__).resolve())},
        "runtime": {"blender": bpy.app.version_string, "python": sys.version.split()[0]},
        "source": {
            "body_object": body.name,
            "body_surface_id": "body.surface.synthetic",
            "body_topology_hash": body_state["topology_hash"],
            "body_semantic_map_hash": body_state["semantic_map_hash"],
            "body_uv_hash": body_state["uv_hash"],
            "body_base_rest_shape_hash": body_state["source_rest_shape_hash"],
        },
        "body": {
            "topology_hash": body_state["topology_hash"],
            "semantic_map_hash": body_state["semantic_map_hash"],
            "uv_hash": body_state["uv_hash"],
            "rest_shape_hash": body_state["rest_shape_hash"],
            "parameters": body_state["parameters"],
            "shape_keys": ["Basis", BODY_WIDTH_PLUS, BODY_WIDTH_MINUS],
            "deformation": "basis_relative_lower_body_depth_v1",
        },
        "pants": {
            "source_object": pants.name,
            "source_id": pants["source_id"],
            "fitted_object": PANTS_FITTED_NAME,
            "source_signature": source_signatures["pants"],
            "semantic": pants_semantic,
            "semantic_map_hash": pants_semantic_hash,
            "waistband_face_ids": json.loads(pants["waistband_face_ids"]),
            "attachment_count": len(pants_records),
            "fit_revision": 1,
            "fitted_rest_shape_hash": pants_fit_hash,
        },
        "belt": {
            "source_variants": {
                variant: {
                    "object": belts[variant].name,
                    "source_id": belts[variant]["source_id"],
                    "source_signature": source_signatures[f"belt_{variant}"],
                    "attachment_count": len(belt_records[variant]),
                }
                for variant in ("A", "B")
            },
            "result_object": BELT_RESULT_NAME,
            "active_variant": selection.active_variant,
            "fit_revision": selection.fit_revision + 1,
            "target_surface_id": "pants.surface.synthetic",
            "target_topology_hash": _topology_hash(bpy.data.objects[PANTS_FITTED_NAME].data),
            "target_semantic_map_hash": pants_semantic_hash,
            "result_rest_shape_hash": belt_a_hash,
        },
        "attachments": {
            "pants": [_attachment_dict(record) for record in pants_records],
            "belt": {
                variant: [_attachment_dict(record) for record in belt_records[variant]]
                for variant in ("A", "B")
            },
        },
        "dependencies": [
            {"from": "body.param.pants_width", "to": "body.evaluated_rest", "kind": "shape_key"},
            {"from": "body.evaluated_rest", "to": "pants.fitted", "kind": "surface_correspondence"},
            {"from": "pants.fitted", "to": "belt.result", "kind": "surface_correspondence"},
            {"from": "belt.source.A|B", "to": "belt.result", "kind": "variant_swap"},
        ],
        "baseline": {
            "body_rest_shape_hash": body_state["rest_shape_hash"],
            "body_topology_hash": body_state["topology_hash"],
            "body_semantic_map_hash": body_state["semantic_map_hash"],
            "body_uv_hash": body_state["uv_hash"],
            "pants_fitted_rest_shape_hash": pants_fit_hash,
            "belt_A_result_rest_shape_hash": belt_a_hash,
            "source_signatures": source_signatures,
        },
        "stage": "baseline",
        "status": "PASS",
    }


def _update_selection(manifest: dict, variant: str) -> None:
    variants = tuple(
        WearableVariant(
            key,
            str(value["source_id"]),
            semantic_sha256(value["source_signature"]),
        )
        for key, value in sorted(manifest["belt"]["source_variants"].items())
    )
    current = WearableSelection(variants, manifest["belt"]["active_variant"], int(manifest["belt"]["fit_revision"]))
    selected = current.select(variant)
    manifest["belt"]["active_variant"] = selected.active_variant
    manifest["belt"]["fit_revision"] = selected.fit_revision


def _protected_state(manifest: dict) -> dict:
    expected = manifest["baseline"]["source_signatures"]
    actual = {
        "body": _source_signature(bpy.data.objects[BODY_NAME]),
        "pants": _source_signature(bpy.data.objects[PANTS_SOURCE_NAME]),
        "belt_A": _source_signature(bpy.data.objects[BELT_SOURCE_NAMES["A"]]),
        "belt_B": _source_signature(bpy.data.objects[BELT_SOURCE_NAMES["B"]]),
    }
    return {
        "expected": expected,
        "actual": actual,
        "unchanged": {key: actual[key] == expected[key] for key in expected},
    }


def _sources_are_separate() -> bool:
    source_names = (PANTS_SOURCE_NAME, BELT_SOURCE_NAMES["A"], BELT_SOURCE_NAMES["B"])
    result = bpy.data.objects.get(BELT_RESULT_NAME)
    if result is None or any(bpy.data.objects.get(name) is None for name in source_names):
        return False
    source_meshes = [bpy.data.objects[name].data for name in source_names]
    return len({id(mesh) for mesh in source_meshes + [result.data]}) == 4


def _current_blend_hash() -> str | None:
    blend_path = Path(bpy.data.filepath) if bpy.data.filepath else None
    return _sha256_file(blend_path) if blend_path is not None and blend_path.exists() else None


def _report(manifest: dict, *, stage: str, checks: dict[str, bool], read_only: bool = False) -> dict:
    blend_hash_before = _current_blend_hash() if read_only else None
    body = bpy.data.objects[BODY_NAME]
    pants = bpy.data.objects[PANTS_SOURCE_NAME]
    pants_fit = bpy.data.objects[PANTS_FITTED_NAME]
    belt_result = bpy.data.objects[BELT_RESULT_NAME]
    belts = {variant: bpy.data.objects[BELT_SOURCE_NAMES[variant]] for variant in ("A", "B")}
    body_state = _body_state(body)
    pants_status = _attachment_report(
        manifest["attachments"]["pants"],
        body,
        surface_id="body.surface.synthetic",
        semantic_revision=manifest["source"]["body_semantic_map_hash"],
    )
    belt_status = {
        variant: _attachment_report(
            manifest["attachments"]["belt"][variant],
            pants_fit,
            surface_id="pants.surface.synthetic",
            semantic_revision=manifest["pants"]["semantic_map_hash"],
        )
        for variant in ("A", "B")
    }
    protected = _protected_state(manifest)
    attachment_ok = pants_status["all_valid"] and all(status["all_valid"] for status in belt_status.values())
    all_checks = all(bool(value) for value in checks.values())
    failure_state = "NONE"
    if not attachment_ok:
        failure_state = "REBIND_REQUIRED"
    elif not all_checks:
        failure_state = "VALIDATION_FAILED"

    stable_payload = {
        "body": {
            "topology_hash": body_state["topology_hash"],
            "semantic_map_hash": body_state["semantic_map_hash"],
            "uv_hash": body_state["uv_hash"],
            "rest_shape_hash": body_state["rest_shape_hash"],
            "pants_width": body_state["parameters"]["pants_width"],
        },
        "pants": {"fitted_rest_shape_hash": _rest_shape_hash(_evaluated_vertices(pants_fit))},
        "belt": {
            "active_variant": manifest["belt"]["active_variant"],
            "result_rest_shape_hash": _rest_shape_hash(_evaluated_vertices(belt_result)),
        },
    }
    blend_hash_after = _current_blend_hash() if read_only else None
    check_items = [
        {"id": key, "status": "PASS" if value else "FAIL"}
        for key, value in sorted(checks.items())
    ]
    return {
        "schema_version": 1,
        "contract": CONTRACT,
        "stage": stage,
        "status": "PASS" if failure_state == "NONE" else "FAIL",
        "failure_state": failure_state,
        "source": {
            "runtime": f"Blender {bpy.app.version_string}",
            "candidate_revision": manifest["candidate_revision"],
            "fixture_id": manifest["fixture"]["id"],
            "builder_sha256": manifest["fixture"]["builder_sha256"],
        },
        "body": {
            "vertex_count": len(body.data.vertices),
            "polygon_count": len(body.data.polygons),
            "topology_hash": body_state["topology_hash"],
            "rest_shape_hash": body_state["rest_shape_hash"],
            "semantic_hash": body_state["semantic_map_hash"],
            "uv_hash": body_state["uv_hash"],
            "parameters": body_state["parameters"],
            "shape_keys": [block.name for block in body.data.shape_keys.key_blocks]
            if body.data.shape_keys is not None
            else [],
        },
        "dependencies": {
            "status": "VALID" if attachment_ok else "REBIND_REQUIRED",
            "state_revision": manifest.get("state_revision", 0),
            "derived_closure": list(_dependency_closure()),
        },
        "pants": {
            "source_object": pants.name,
            "fitted_object": pants_fit.name,
            "source_signature": _source_signature(pants),
            "fitted_rest_shape_hash": _rest_shape_hash(_evaluated_vertices(pants_fit)),
            "fit_revision": manifest["pants"]["fit_revision"],
            "attachment_status": pants_status,
        },
        "belt": {
            "active_variant": manifest["belt"]["active_variant"],
            "result_object": belt_result.name,
            "result_rest_shape_hash": _rest_shape_hash(_evaluated_vertices(belt_result)),
            "fit_revision": manifest["belt"]["fit_revision"],
            "source_signatures": {variant: _source_signature(belts[variant]) for variant in ("A", "B")},
            "attachment_status": belt_status,
        },
        "attachments": {"pants": pants_status, "belt": belt_status},
        "checks": check_items,
        "check_map": checks,
        "protected_sources": protected,
        "semantic_payload": stable_payload,
        "semantic_hash": semantic_sha256(stable_payload),
        "observation": {
            "read_only": read_only,
            "blend_sha256_before": blend_hash_before,
            "blend_sha256_after": blend_hash_after,
            "mutated": (blend_hash_before != blend_hash_after) if read_only else None,
        },
    }


def _write_stage(out: Path, manifest: dict, report: dict, *, manifest_name: str, report_name: str) -> None:
    _write_json(out / manifest_name, manifest)
    _write_json(out / report_name, report)


def mode_build(args: dict[str, str]) -> dict:
    out = Path(args["out"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    body, pants, belts = _create_scene()
    body_state = _body_state(body)
    body_semantic = body_state["semantic"]
    body_semantic_hash = body_state["semantic_map_hash"]
    body_faces = set(index for values in json.loads(body["semantic_regions"]).values() for index in values)

    pants_records = _bind(
        _mesh_vertices(pants.data),
        body,
        target_surface_id="body.surface.synthetic",
        target_semantic_revision=body_semantic_hash,
        candidate_faces=body_faces,
        normal_offset=0.045,
        attachment_prefix="pants.fit",
    )
    pants_fit = _copy_object(pants, PANTS_FITTED_NAME, visible=True)
    pants_fit["source_id"] = pants["source_id"]
    pants_fit["surface_id"] = "pants.surface.synthetic"
    pants_fit["semantic_derivation"] = "synthetic.pants.regions.v1"
    pants_fit["semantic_regions"] = pants["semantic_regions"]
    pants_fit["semantic_map_hash"] = ""
    _set_vertices(
        pants_fit,
        _evaluate_records(
            pants_records,
            body,
            surface_id="body.surface.synthetic",
            semantic_revision=body_semantic_hash,
        ),
    )
    pants_semantic, pants_semantic_hash = _pants_semantic(pants_fit)
    pants_fit["semantic_map_hash"] = pants_semantic_hash
    waistband_faces = set(json.loads(pants["waistband_face_ids"]))

    belt_records = {
        variant: _bind(
            _mesh_vertices(belts[variant].data),
            pants_fit,
            target_surface_id="pants.surface.synthetic",
            target_semantic_revision=pants_semantic_hash,
            candidate_faces=waistband_faces,
            normal_offset=0.018 if variant == "A" else 0.032,
            attachment_prefix=f"belt.{variant}.fit",
        )
        for variant in ("A", "B")
    }
    belt_result = _copy_object(belts["A"], BELT_RESULT_NAME, visible=True)
    belt_result["surface_id"] = "belt.surface.synthetic.result"
    belt_result["active_variant"] = "A"
    belt_result["fit_method"] = "surface_correspondence"
    _set_vertices(
        belt_result,
        _evaluate_records(
            belt_records["A"],
            pants_fit,
            surface_id="pants.surface.synthetic",
            semantic_revision=pants_semantic_hash,
        ),
    )
    belt_a_hash = _rest_shape_hash(_evaluated_vertices(belt_result))
    belt_probe = _copy_object(belts["B"], "CK_Belt_Baseline_Probe", visible=False)
    _set_vertices(
        belt_probe,
        _evaluate_records(
            belt_records["B"],
            pants_fit,
            surface_id="pants.surface.synthetic",
            semantic_revision=pants_semantic_hash,
        ),
    )
    belt_b_hash = _rest_shape_hash(_evaluated_vertices(belt_probe))
    _remove_object(belt_probe.name)

    manifest = _asset_manifest(
        body,
        pants,
        belts,
        body_state,
        pants_semantic,
        pants_semantic_hash,
        pants_records,
        belt_records,
        _rest_shape_hash(_evaluated_vertices(pants_fit)),
        belt_a_hash,
    )
    manifest["state_revision"] = 0
    manifest["baseline"]["belt_B_result_rest_shape_hash"] = belt_b_hash
    manifest["belt"]["result_variant_hashes"] = {"A": belt_a_hash, "B": belt_b_hash}
    _store_manifest(manifest)
    pants_status = _attachment_report(
        manifest["attachments"]["pants"],
        body,
        surface_id="body.surface.synthetic",
        semantic_revision=body_semantic_hash,
    )
    belt_status = {
        variant: _attachment_report(
            manifest["attachments"]["belt"][variant],
            pants_fit,
            surface_id="pants.surface.synthetic",
            semantic_revision=pants_semantic_hash,
        )
        for variant in ("A", "B")
    }
    report = _report(
        manifest,
        stage="baseline",
        checks={
            "fixture_builder_created": True,
            "body_topology_preserved": body_state["topology_hash"] == manifest["source"]["body_topology_hash"],
            "body_semantic_mapping_preserved": body_state["semantic_map_hash"] == manifest["source"]["body_semantic_map_hash"],
            "body_uv_contract_preserved": body_state["uv_hash"] == manifest["source"]["body_uv_hash"],
            "sources_are_separate": _sources_are_separate(),
            "pants_attachments_bound": pants_status["all_valid"],
            "belt_A_attachments_bound": belt_status["A"]["all_valid"],
            "belt_B_attachments_bound": belt_status["B"]["all_valid"],
            "shape_key_contract_present": BODY_WIDTH_PLUS in manifest["body"]["shape_keys"] and BODY_WIDTH_MINUS in manifest["body"]["shape_keys"],
        },
    )
    _write_stage(out, manifest, report, manifest_name="manifest_baseline.json", report_name="report_baseline.json")
    _save(out / "candidate_baseline.blend")
    print("CK_BUILD", json.dumps({"status": report["status"], "pants_attachments": len(pants_records), "belt_attachments": len(belt_records["A"])}))
    return report


def _apply_edit(args: dict[str, str], *, stage: str, width: float, variant: str, output_name: str) -> dict:
    out = Path(args["out"]).resolve()
    if variant not in BELT_SOURCE_NAMES:
        raise ValueError(f"unsupported belt variant: {variant!r}")
    manifest = _load_manifest()
    body = bpy.data.objects[BODY_NAME]
    pants = bpy.data.objects[PANTS_SOURCE_NAME]
    pants_fit = bpy.data.objects[PANTS_FITTED_NAME]
    old_pants_hash = _rest_shape_hash(_evaluated_vertices(pants_fit))
    old_belt_hash = _rest_shape_hash(_evaluated_vertices(bpy.data.objects[BELT_RESULT_NAME]))
    actual_width = _set_width(body, width)
    body_state = _body_state(body)
    pants_records = manifest["attachments"]["pants"]
    _set_vertices(
        pants_fit,
        _evaluate_records(
            pants_records,
            body,
            surface_id="body.surface.synthetic",
            semantic_revision=manifest["source"]["body_semantic_map_hash"],
        ),
    )
    belt_result = _copy_object(bpy.data.objects[BELT_SOURCE_NAMES[variant]], BELT_RESULT_NAME, visible=True)
    belt_result["surface_id"] = "belt.surface.synthetic.result"
    belt_result["active_variant"] = variant
    belt_result["fit_method"] = "surface_correspondence"
    belt_records = manifest["attachments"]["belt"][variant]
    belt_hash_coordinates = _evaluate_records(
        belt_records,
        pants_fit,
        surface_id="pants.surface.synthetic",
        semantic_revision=manifest["pants"]["semantic_map_hash"],
    )
    _set_vertices(belt_result, belt_hash_coordinates)
    belt_hash = _rest_shape_hash(_evaluated_vertices(belt_result))
    manifest["stage"] = stage
    manifest["state_revision"] = int(manifest.get("state_revision", 0)) + 1
    manifest["body"]["rest_shape_hash"] = body_state["rest_shape_hash"]
    manifest["body"]["parameters"] = body_state["parameters"]
    manifest["pants"]["fit_revision"] = int(manifest["pants"]["fit_revision"]) + 1
    manifest["pants"]["fitted_rest_shape_hash"] = _rest_shape_hash(_evaluated_vertices(pants_fit))
    _update_selection(manifest, variant)
    manifest["belt"]["result_rest_shape_hash"] = belt_hash
    manifest["belt"]["result_variant_hashes"][variant] = belt_hash
    _store_manifest(manifest)
    baseline = manifest["baseline"]
    checks = {
        "body_topology_preserved": body_state["topology_hash"] == baseline["body_topology_hash"],
        "body_semantic_mapping_preserved": body_state["semantic_map_hash"] == baseline["body_semantic_map_hash"],
        "body_uv_contract_preserved": body_state["uv_hash"] == baseline["body_uv_hash"],
        "body_edit_changed_rest_shape": body_state["rest_shape_hash"] != baseline["body_rest_shape_hash"],
        "pants_refit_changed_from_previous": manifest["pants"]["fitted_rest_shape_hash"] != old_pants_hash,
        "belt_refit_changed_after_body_edit": belt_hash != baseline["belt_B_result_rest_shape_hash"] if variant == "B" else belt_hash != baseline["belt_A_result_rest_shape_hash"],
        "belt_swap_changed_result": belt_hash != old_belt_hash,
        "source_state_protected": all(_protected_state(manifest)["unchanged"].values()),
        "declared_dependency_closure_present": set(_dependency_closure()) == {"body.evaluated_rest", "pants.fitted", "belt.result"},
        "active_variant_recorded": manifest["belt"]["active_variant"] == variant,
    }
    report = _report(manifest, stage=stage, checks=checks)
    _write_stage(out, manifest, report, manifest_name=f"manifest_{stage}.json", report_name=f"report_{stage}.json")
    _save(out / output_name)
    print("CK_EDIT", json.dumps({"stage": stage, "status": report["status"], "width": actual_width, "variant": variant}))
    return report


def mode_edit(args: dict[str, str]) -> dict:
    return _apply_edit(args, stage="edited", width=float(args.get("pants_width", "1.05")), variant=args.get("variant", "B"), output_name="candidate_edited.blend")


def mode_reedit(args: dict[str, str]) -> dict:
    return _apply_edit(args, stage="reedited", width=float(args.get("pants_width", "0.96")), variant=args.get("variant", "A"), output_name="candidate_reedited.blend")


def mode_restore(args: dict[str, str]) -> dict:
    out = Path(args["out"]).resolve()
    manifest = _load_manifest()
    body = bpy.data.objects[BODY_NAME]
    pants_fit = bpy.data.objects[PANTS_FITTED_NAME]
    _set_width(body, 1.0)
    body_state = _body_state(body)
    _set_vertices(
        pants_fit,
        _evaluate_records(
            manifest["attachments"]["pants"],
            body,
            surface_id="body.surface.synthetic",
            semantic_revision=manifest["source"]["body_semantic_map_hash"],
        ),
    )
    belt_result = _copy_object(bpy.data.objects[BELT_SOURCE_NAMES["A"]], BELT_RESULT_NAME, visible=True)
    belt_result["surface_id"] = "belt.surface.synthetic.result"
    belt_result["active_variant"] = "A"
    belt_result["fit_method"] = "surface_correspondence"
    _set_vertices(
        belt_result,
        _evaluate_records(
            manifest["attachments"]["belt"]["A"],
            pants_fit,
            surface_id="pants.surface.synthetic",
            semantic_revision=manifest["pants"]["semantic_map_hash"],
        ),
    )
    pants_hash = _rest_shape_hash(_evaluated_vertices(pants_fit))
    belt_hash = _rest_shape_hash(_evaluated_vertices(belt_result))
    manifest["stage"] = "restored"
    manifest["state_revision"] = int(manifest.get("state_revision", 0)) + 1
    manifest["body"]["rest_shape_hash"] = body_state["rest_shape_hash"]
    manifest["body"]["parameters"] = body_state["parameters"]
    manifest["pants"]["fit_revision"] = int(manifest["pants"]["fit_revision"]) + 1
    manifest["pants"]["fitted_rest_shape_hash"] = pants_hash
    _update_selection(manifest, "A")
    manifest["belt"]["result_rest_shape_hash"] = belt_hash
    manifest["belt"]["result_variant_hashes"]["A"] = belt_hash
    _store_manifest(manifest)
    baseline = manifest["baseline"]
    checks = {
        "body_restored": body_state["rest_shape_hash"] == baseline["body_rest_shape_hash"],
        "body_topology_preserved": body_state["topology_hash"] == baseline["body_topology_hash"],
        "body_semantic_mapping_preserved": body_state["semantic_map_hash"] == baseline["body_semantic_map_hash"],
        "body_uv_contract_preserved": body_state["uv_hash"] == baseline["body_uv_hash"],
        "pants_restored": pants_hash == baseline["pants_fitted_rest_shape_hash"],
        "belt_A_restored": belt_hash == baseline["belt_A_result_rest_shape_hash"],
        "active_variant_restored": manifest["belt"]["active_variant"] == "A",
        "source_state_protected": all(_protected_state(manifest)["unchanged"].values()),
    }
    report = _report(manifest, stage="restored", checks=checks)
    _write_stage(out, manifest, report, manifest_name="manifest_restored.json", report_name="report_restored.json")
    _save(out / "candidate_final.blend")
    print("CK_RESTORE", json.dumps({"status": report["status"], "all_restored": all(checks.values())}))
    return report


def mode_verify(args: dict[str, str]) -> dict:
    """Read actual scene state without saving or changing the .blend."""
    out = Path(args["out"]).resolve()
    label = args.get("label", "final_readonly")
    manifest = _load_manifest()
    baseline = manifest["baseline"]
    state = _body_state(bpy.data.objects[BODY_NAME])
    if manifest.get("stage") == "corrupt":
        corrupt_status = _attachment_report(
            manifest["attachments"]["belt"]["A"],
            bpy.data.objects[PANTS_FITTED_NAME],
            surface_id="pants.surface.synthetic",
            semantic_revision=manifest["pants"]["semantic_map_hash"],
        )
        checks = {
            "corruption_marker_present": bool(manifest.get("corruption", {}).get("attachment_id")),
            "stale_attachment_rejected": corrupt_status["status"] == "REBIND_REQUIRED",
            "protected_sources_unchanged": all(_protected_state(manifest)["unchanged"].values()),
        }
    else:
        checks = {
            "final_artifact_readable": True,
            "final_stage_restored": manifest.get("stage") == "restored",
            "body_restored": state["rest_shape_hash"] == baseline["body_rest_shape_hash"],
            "pants_restored": _rest_shape_hash(_evaluated_vertices(bpy.data.objects[PANTS_FITTED_NAME])) == baseline["pants_fitted_rest_shape_hash"],
            "belt_A_restored": _rest_shape_hash(_evaluated_vertices(bpy.data.objects[BELT_RESULT_NAME])) == baseline["belt_A_result_rest_shape_hash"],
            "active_variant_restored": manifest["belt"]["active_variant"] == "A",
            "protected_sources_unchanged": all(_protected_state(manifest)["unchanged"].values()),
        }
    report = _report(manifest, stage=label, checks=checks, read_only=True)
    if manifest.get("stage") == "corrupt":
        report["checks"].append({"id": "fail_closed_corruption", "status": "PASS" if report["failure_state"] == "REBIND_REQUIRED" else "FAIL"})
        report["check_map"]["fail_closed_corruption"] = report["failure_state"] == "REBIND_REQUIRED"
    _write_json(out / f"report_{label}.json", report)
    print("CK_VERIFY", json.dumps({"status": report["status"], "read_only": True, "mutated": report["observation"]["mutated"], "label": label}))
    return report


def mode_corrupt(args: dict[str, str]) -> dict:
    out = Path(args["out"]).resolve()
    manifest = _load_manifest()
    records = list(manifest["attachments"]["belt"]["A"])
    if not records:
        raise RuntimeError("belt A attachment records are missing")
    attachment_id = records[0]["attachment_id"]
    records[0]["target_topology_revision"] = "corrupt-topology-revision"
    manifest["attachments"]["belt"]["A"] = records
    manifest["stage"] = "corrupt"
    manifest["corruption"] = {
        "kind": "target_topology_revision",
        "attachment_id": attachment_id,
        "expected": "REBIND_REQUIRED",
    }
    _store_manifest(manifest)
    status = _attachment_report(
        records,
        bpy.data.objects[PANTS_FITTED_NAME],
        surface_id="pants.surface.synthetic",
        semantic_revision=manifest["pants"]["semantic_map_hash"],
    )
    report = _report(
        manifest,
        stage="corrupt_injection",
        checks={
            "corruption_injected": True,
            "stale_attachment_rejected": status["status"] == "REBIND_REQUIRED",
            "protected_sources_unchanged": all(_protected_state(manifest)["unchanged"].values()),
        },
    )
    _write_json(out / "report_corrupt_injection.json", report)
    _save(out / "candidate_corrupt.blend")
    print("CK_CORRUPT", json.dumps({"status": report["status"], "failure_state": report["failure_state"], "attachment": attachment_id}))
    return report


def _run_blender(blend: Path | None, mode: str, args: dict[str, str], log_path: Path, **extra: str) -> dict:
    command = [bpy.app.binary_path, "-b", "--factory-startup"]
    display_input = "--factory-startup" if blend is None else blend.name
    if blend is not None:
        command.append(str(blend))
    command += ["--python", str(Path(__file__).resolve()), "--", "--mode", mode, "--out", str(args["out"])]
    for key, value in extra.items():
        command += [f"--{key.replace('_', '-')}", str(value)]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, cwd=str(ROOT), text=True)
    return {
        "mode": mode,
        "input": display_input,
        "returncode": completed.returncode,
        "log": log_path.relative_to(Path(args["out"]).resolve()).as_posix(),
    }


def _load_report(out: Path, name: str) -> dict:
    path = out / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def mode_roundtrip(args: dict[str, str]) -> dict:
    out = Path(args["out"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    steps = []
    steps.append(_run_blender(None, "build", args, out / "build.log"))
    steps.append(_run_blender(out / "candidate_baseline.blend", "edit", args, out / "edit.log", pants_width="1.05", variant="B"))
    steps.append(_run_blender(out / "candidate_edited.blend", "reedit", args, out / "reedit.log", pants_width="0.96", variant="A"))
    steps.append(_run_blender(out / "candidate_reedited.blend", "restore", args, out / "restore.log"))
    steps.append(_run_blender(out / "candidate_final.blend", "verify", args, out / "verify.log", label="final_readonly"))
    steps.append(_run_blender(out / "candidate_baseline.blend", "corrupt", args, out / "corrupt.log"))
    steps.append(_run_blender(out / "candidate_corrupt.blend", "verify", args, out / "corrupt_verify.log", label="corrupt_readonly"))

    reports = {
        name: _load_report(out, f"report_{name}.json")
        for name in ("baseline", "edited", "reedited", "restored", "final_readonly", "corrupt_injection", "corrupt_readonly")
    }
    baseline = reports["baseline"]
    edited = reports["edited"]
    reedited = reports["reedited"]
    restored = reports["restored"]
    final_readonly = reports["final_readonly"]
    corrupt = reports["corrupt_readonly"]
    source_protected = all(
        report.get("protected_sources", {}).get("unchanged", {}).get(key, False)
        for report in (baseline, edited, reedited, restored, final_readonly)
        for key in ("body", "pants", "belt_A", "belt_B")
    )
    proofs = {
        "public_fixture_builder": baseline.get("source", {}).get("fixture_id") == FIXTURE_ID,
        "separate_authoring_sources": baseline.get("check_map", {}).get("sources_are_separate", False),
        "pants_to_body_attachment": baseline.get("attachments", {}).get("pants", {}).get("all_valid", False),
        "belt_to_pants_attachment": all(
            baseline.get("attachments", {}).get("belt", {}).get(variant, {}).get("all_valid", False)
            for variant in ("A", "B")
        ),
        "supported_deformation_changed_body": baseline.get("body", {}).get("rest_shape_hash") != edited.get("body", {}).get("rest_shape_hash"),
        "supported_deformation_refit_pants": baseline.get("pants", {}).get("fitted_rest_shape_hash") != edited.get("pants", {}).get("fitted_rest_shape_hash"),
        "supported_deformation_refit_belt": edited.get("check_map", {}).get("belt_refit_changed_after_body_edit", False),
        "belt_swap_A_to_B": edited.get("check_map", {}).get("belt_swap_changed_result", False),
        "belt_swap_back_B_to_A": reedited.get("check_map", {}).get("belt_swap_changed_result", False),
        "fresh_process_reedit": reedited.get("check_map", {}).get("pants_refit_changed_from_previous", False),
        "fresh_process_restore": restored.get("status") == "PASS",
        "fresh_process_read_only_verify": final_readonly.get("status") == "PASS" and final_readonly.get("observation", {}).get("mutated") is False,
        "source_state_protected": source_protected,
        "fail_closed_corruption": corrupt.get("failure_state") == "REBIND_REQUIRED" and corrupt.get("observation", {}).get("mutated") is False,
        "scene_sensitive_report": baseline.get("semantic_hash") != edited.get("semantic_hash"),
    }
    evidence = {
        "contract": CONTRACT,
        "candidate_revision": _candidate_revision(),
        "runtime": {"blender": bpy.app.version_string, "python": sys.version.split()[0]},
        "fixture": {"id": FIXTURE_ID, "builder_sha256": _sha256_file(Path(__file__).resolve())},
        "processes": steps,
        "statuses": {name: report.get("status") for name, report in reports.items()},
        "proofs": proofs,
        "protected_invariants": {
            "topology": all(report.get("check_map", {}).get(key, True) for report in (edited, reedited, restored) for key in ("body_topology_preserved", "body_semantic_mapping_preserved", "body_uv_contract_preserved")),
            "source_state_unchanged": source_protected,
            "core_bpy_free": _core_is_bpy_free(),
        },
        "learning_gate": {
            "status": "PASS",
            "decision": "basis-relative lower-body depth deformation is a synthetic-fixture probe only; it is not promoted as a general fitting rule",
            "unsupported_generalization": True,
        },
        "unsupported": [
            "identity fitting and private ss assets",
            "full cloth or pattern sewing",
            "expressions, tracking, consumer export, and production visual approval",
        ],
        "status": "PASS" if all(proofs.values()) and all(value == "PASS" for key, value in evidence_statuses(reports).items() if key not in {"corrupt_injection", "corrupt_readonly"}) and corrupt.get("failure_state") == "REBIND_REQUIRED" else "FAIL",
        "promotion": "SCOPED_HOST_PASS" if all(proofs.values()) else "UNVERIFIED",
        "reports": {name: f"report_{name}.json" for name in reports},
        "artifacts": [name for name in ("candidate_baseline.blend", "candidate_edited.blend", "candidate_reedited.blend", "candidate_final.blend", "candidate_corrupt.blend") if (out / name).exists()],
    }
    _write_json(out / "roundtrip_evidence.json", evidence)
    print("CK_ROUNDTRIP", json.dumps({"status": evidence["status"], "promotion": evidence["promotion"], "proofs": proofs}))
    return evidence


def evidence_statuses(reports: dict[str, dict]) -> dict[str, str | None]:
    return {name: report.get("status") for name, report in reports.items()}


MODES = {
    "build": mode_build,
    "edit": mode_edit,
    "reedit": mode_reedit,
    "restore": mode_restore,
    "verify": mode_verify,
    "corrupt": mode_corrupt,
    "roundtrip": mode_roundtrip,
}


def main() -> None:
    args = _args()
    mode = args["mode"]
    if mode not in MODES:
        raise SystemExit(f"unsupported mode: {mode}")
    MODES[mode](args)


if __name__ == "__main__":
    main()
