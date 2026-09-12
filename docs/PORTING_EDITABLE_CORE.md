# Porting the bounded editable core

This document describes how to migrate the previously exercised local Blender editable-core implementation into this public repository without pretending that the old local files are already audited here.

## Current state

The repository now has public-safe architecture, schemas, and a host-independent runtime core.

The previous local Blender run reportedly provided:

- body parameter edits;
- SurfaceAttachment evaluation;
- rest rig / fitted garment / scalp-hair recomputation;
- hair A/B, sleeve, and front-bang edits;
- read-only character reporting;
- fail-closed `REBIND_REQUIRED`;
- fresh-process roundtrip.

Those reports are useful migration inputs, not source code present in this repository.

## Porting order

1. Inspect the exact local implementation and evidence in its original workspace.
2. Record exact source hashes and Blender version.
3. Remove personal paths, provider/session data, raw logs, and non-redistributable assets.
4. Map reusable host-independent logic onto `src/character_kernel/`.
5. Put Blender-specific access behind a narrow adapter instead of mixing `bpy` state access into core correspondence/hash logic.
6. Preserve accepted behavior with tests before refactoring.
7. Add a redistribution-safe synthetic Blender fixture.
8. Re-run:
   - baseline report;
   - supported body edit;
   - garment/hair recomputation;
   - local hair/garment edits;
   - deliberate corruption;
   - save -> fresh process -> report -> re-edit -> restore.
9. Only after parity is proven, mark the ported implementation as replacing the local prototype.

## Required parity table

| Capability | Local evidence | Public port requirement |
|---|---|---|
| Surface correspondence | reported PASS | focused unit tests + Blender fixture |
| revision mismatch | reported `REBIND_REQUIRED` | deterministic fail-closed test |
| body parameter edit | reported PASS | actual rest-shape change with stable topology |
| rest rig update | reported PASS | declared affected joints updated/fresh |
| fitted garment | reported PASS | recompute without rewriting garment authoring source |
| scalp/hair roots | reported PASS | attachment validity + visual review |
| report | reported deterministic | actual scene sensitivity + persistent non-mutation |
| fresh-process edit | reported PASS | synthetic public fixture roundtrip |

## Non-goals during port

Do not add identity fitting, full garment simulation, expression systems, consumer export, or a new operator/harness merely to make the repository look complete.

The port is complete when the public-safe implementation reproduces the bounded editable-core behavior with evidence tied to exact repository revisions.
