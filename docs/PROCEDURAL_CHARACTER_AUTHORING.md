# Procedural Character Authoring

Status: durable design contract. Host- and asset-specific claims still require current evidence.

## 1. Goal

Build characters as editable systems rather than final meshes.

The authoring master should preserve:

- canonical topology identity;
- body/face parameter source;
- semantic regions;
- attachment definitions;
- rig schema;
- garment edit source;
- hair guides and style parameters;
- accepted manual correction layers;
- dependency state and revisions.

Derived geometry should be reproducible from those sources.

## 2. Three layers

### Authoring source

Persistent editable authority:

- canonical body topology;
- body parameters / shape deltas;
- semantic regions;
- joint-anchor definitions;
- rig schema;
- garment parameters or editable source;
- garment attachment mapping;
- scalp region;
- hair guide components and style parameters;
- hair-root attachment data;
- accepted manual correction layers.

### Derived artifacts

Rebuildable state:

- evaluated neutral/rest body;
- body-specific joint coordinates;
- rest armature instance;
- bind/weights/correctives produced from current source;
- fitted garment geometry;
- hair-root positions and generated hair geometry;
- collision proxies;
- renders and previews.

### Runtime export

Consumer-specific output:

- triangulated or merged meshes;
- atlases;
- LODs;
- engine-specific skeleton/material packaging;
- VRM/glTF/FBX or other delivery formats.

Do not push runtime optimization back into authoring source.

## 3. Fixed topology means stable identity, not fixed shape

Within a topology family, ordered connectivity/index meaning remains stable while rest geometry may change.

Keep separate:

- `topology_hash` — ordered connectivity/index contract;
- `rest_shape_hash` — evaluated neutral/rest coordinates;
- `semantic_hash` — semantic IDs/regions;
- `uv_hash` — face-corner UV contract;
- `rig_schema_hash` — semantic bones, hierarchy, axis/rest conventions;
- `rig_instance_hash` / bind revision — current body-specific transforms/bind inputs;
- `source_content_hash` — normalized editable-source content.

A supported body edit normally expects:

```text
before.topology_hash == after.topology_hash
before.rest_shape_hash != after.rest_shape_hash
```

plus explicit checks for semantic/UV compatibility.

## 4. Surface-relative attachment

`SurfaceAttachment` is a shared correspondence primitive, not a universal solver.

Useful targets include:

- hair roots;
- garment fit points;
- accessory sockets;
- some landmarks/joint supports.

Minimal conceptual fields:

```text
attachment_id
target_surface_id
target_topology_revision
target_semantic_revision
coordinate representation
normal/frame offset
space/unit convention
```

A triangle representation may use deterministic face identity + barycentric weights. A quad master must not depend on incidental triangulation unless that triangulation is versioned as part of the attachment contract.

Do not use world XYZ alone as durable attachment authority.

Joint solving may additionally require vertex-set means, helper regions, regressors, anatomical constraints, roll/orientation rules, or other typed strategies.

## 5. Body parameterization

Start with a small explicit parameter set and grow only from real character needs.

A basic linear view is:

```text
V(beta) = V0 + sum(beta_i * DeltaV_i)
```

but parameter semantics are more important than the formula.

Each parameter should define:

- name and domain;
- units or normalized interpretation;
- reference measurement;
- affected source region;
- parameter -> deformation mapping;
- incompatible ranges;
- dependency invalidation/rebuild set.

Do not assume parameter names form an orthogonal basis.

## 6. Rig contract

Keep stable:

- bone semantic IDs;
- hierarchy;
- local-axis/rest-pose convention;
- deform/non-deform role;
- socket/control schema.

Allow body-specific:

- joint coordinates;
- bone lengths;
- solved rest transforms.

Body identity changes may invalidate joint anchors, rest rig, bind inputs, fitted assets, collision state, and correctives. Pose changes are a different operation.

## 7. Hair

Hair authoring source should preserve component identity and editable guides.

Example:

```text
HairElementGraph
  bangs
  side_L
  side_R
  back
  tail_*
  ahoge
    -> guide source
    -> root attachment
    -> style parameters
    -> material
    -> optional local rig/dynamics
```

Local edits should update only the target component source and declared downstream geometry/collision/export state.

Save/reload acceptance must prove that guide identity and parameters survive a fresh process.

## 8. Garments

Do not force every garment into one representation.

- `SURFACE_CONFORM` — fitted shirt, tights, inner layers.
- `PATTERN_PARAMETRIC` — garments whose panel/seam/length/flare semantics matter.
- `RIGID_SHELL` — rigid accessories/armor-like assets.
- `HYBRID` — mixed fitted and loose regions.

For fitted garments, persist correspondence rather than re-running blind nearest-surface fitting every time.

For pattern-parametric garments, panel/seam/design source is more important than preserving derived tessellation.

## 9. Identity fitting

When character references are ready:

```text
reference normalization
-> camera/scale alignment
-> semantic landmarks
-> silhouette constraints
-> solve existing body/face parameters
-> residual local correction
-> hair/style fit
-> garment fit
-> source-view comparison
```

Generated 3D can be scaffold/target/hypothesis, not canonical topology by default.

Keep visible original reference evidence above generated hidden-side hypotheses.

## 10. Read-only scene reporting

A `character_report`-style inspector should read actual scene state and distinguish source Blender data from evaluated geometry.

Useful fields include:

- Blender/runtime version;
- source/fixture revision;
- topology/rest-shape/semantic/UV revisions;
- body parameters;
- rig schema and rig-instance/bind revisions;
- missing anchors/references;
- garment source/fit revisions;
- hair guide/attachment revisions;
- dependency freshness / `REBIND_REQUIRED` state.

A deterministic report is useful only if it is sensitive to real scene changes and does not mutate authoring state.

## 11. Scope discipline

Do not build a full human generator, all-garment solver, complete expression system, or multi-DCC pipeline before real fixtures require them.

The default path is:

1. one topology family;
2. one or two body parameters;
3. one rig solve path;
4. one fitted garment;
5. one modular hair fixture;
6. deterministic report/validation;
7. fresh-process roundtrip;
8. then controlled identity fitting.

## 12. Evidence boundary

Historical bounded runs reported an editable dependency core on Blender, including valid/invalid attachment handling and fresh-process editing. Those reports are useful prior evidence, not proof that every implementation in this repository has passed the same test.

See `EVIDENCE_MODEL.md` and `ACCEPTANCE.md`.
