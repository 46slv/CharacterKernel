# Architecture

## Dependency model

```text
Body parameter source
  -> evaluated neutral/rest body
      -> joint support/anchors -> rest armature instance -> bind state
      -> fitted-garment correspondence -> fitted garment
      -> scalp correspondence -> hair roots -> generated hair
      -> collision/measurement proxies

Hair source -------------------------------> generated hair
Garment source ----------------------------> fitted/draped garment
Manual accepted deltas --------------------> protected correction layer
```

## Source vs derived

A change is defined by three sets:

- `source_write_set` — editable authority intentionally changed;
- `derived_invalidation_set` — downstream state that is now stale;
- `protected_source_set` — source that must remain byte/semantic equivalent.

Do not require derived meshes to stay unchanged when their dependencies legitimately changed.

## Attachment strategy

Surface-relative attachment is a correspondence layer. Solver behavior belongs to the subsystem using it.

Examples:

- hair root: point/frame on scalp;
- fitted garment vertex/control: point/frame on fit surface;
- joint: may use a surface point, helper region, vertex-set aggregate, or regressor;
- rigid accessory: socket transform.

The schema must carry enough version identity to reject stale correspondence.

## Hashing and revisions

Do not conflate:

- topology identity;
- evaluated neutral/rest shape;
- semantic mapping;
- UV contract;
- rig schema;
- rig instance;
- bind state;
- source content.

Hash canonicalization must itself be versioned.

## Manual corrections

Accepted manual weights, correctives, guides, or local shape fixes are authoring source.

Rebuild systems must either:
- preserve/reapply them under a valid correspondence contract; or
- fail with an explicit unresolved state.

Silently replacing accepted manual edits is invalid.

## Serialization

An editable `.blend` is necessary but not sufficient. Machine-readable manifests/reports should expose the semantic state needed by agents and validators.

Persistence acceptance requires:
- Save As;
- close process;
- open in a fresh Blender process;
- report;
- repeat supported edits;
- restore baseline or another accepted source state.
