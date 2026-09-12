# CharacterKernel agent rules

This file is a map, not a manual.

## Routing

- Character authoring architecture or data contracts -> `docs/PROCEDURAL_CHARACTER_AUTHORING.md`
- Dependency/source/derived boundaries -> `docs/ARCHITECTURE.md`
- A local edit or repair -> `docs/CHANGE_PROTOCOL.md`
- Pass/fail decisions -> `docs/ACCEPTANCE.md`
- Evidence/provenance questions -> `docs/EVIDENCE_MODEL.md`
- Repeated operational flow -> `skills/character-3d-authoring/SKILL.md`

Read only what the current task needs.

## Authority

1. Current user instruction and explicit scope.
2. Current repository state, tests, fixtures, and live Blender/runtime evidence.
3. Current official Blender/API documentation for version-sensitive behavior.
4. Durable docs in this repository.
5. Historical research and inference.

Do not upgrade a research proposal or old run summary into current runtime truth.

## Core invariants

- Generated mesh/reference output is never automatically the canonical topology.
- Authoring source, derived artifacts, and runtime exports remain separate.
- Topology identity, rest-shape identity, semantic mapping, UV contract, rig schema, and rig instance/bind are distinct.
- Supported body edits must recompute affected dependencies or fail closed; stale success is not success.
- Attachment validity is not equivalent to visual quality, collision quality, or anatomical correctness.
- Manual accepted deltas are protected authoring source; do not silently overwrite them during regeneration.
- Local edits must preserve non-target source state and may modify only declared downstream dependency closure.
- Save/reload/fresh-process re-edit is part of acceptance for editable authoring state.
- Never delete body source geometry merely to hide garment penetration.
- Do not destructively merge/triangulate/atlas authoring masters just to satisfy a runtime export.

## Public repository guard

Never commit:
- credentials, tokens, cookies, account data;
- personal absolute paths, machine names, raw session logs;
- private images/conversations;
- unreviewed binary evidence from a local machine.

Use synthetic fixtures and sanitized summaries unless redistribution is explicitly allowed.

## Delivery

For non-trivial changes:
- use a task branch;
- keep diffs narrow;
- add or update focused tests/validators when behavior can be mechanized;
- document remaining unsupported cases;
- open a Draft PR rather than merging by default.
