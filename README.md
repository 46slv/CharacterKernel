# CharacterKernel

CharacterKernel is a procedural, modular authoring foundation for reusable 3D characters.

The repository treats editable source as the product: stable topology, semantic regions, body parameters, rig compatibility, surface-relative attachments, modular hair and garments, deterministic validation, and fresh-process re-editability. Runtime exports are derived artifacts, not the authoring source of truth.

## Start here

For Codex and other coding agents:

1. Read `AGENTS.md`.
2. For implementation or repair work, read `skills/character-3d-authoring/SKILL.md`.
3. Read only the relevant docs:
   - `docs/PROCEDURAL_CHARACTER_AUTHORING.md` — durable authoring rules and architecture.
   - `docs/ARCHITECTURE.md` — source/derived/runtime boundaries and dependency model.
   - `docs/CHANGE_PROTOCOL.md` — local edits, invalidation, recomputation, rollback.
   - `docs/ACCEPTANCE.md` — structural, visual, persistence, and fail-closed gates.
   - `docs/EVIDENCE_MODEL.md` — what counts as evidence and what does not.
4. Treat the current repository, current Blender scene/runtime, tests, and current user instruction as higher authority than historical research.

## Current scope

The current proven direction is a Blender-first fixed-topology character kernel with:

- explicit body parameters;
- semantic regions;
- versioned surface-relative attachments;
- body-specific rest rig solving;
- fitted-garment recomputation;
- scalp/hair attachment and local hair edits;
- read-only scene reporting;
- save -> fresh Blender process -> re-edit validation.

Historical bounded runs reported `EDITABLE_CORE_READY`, but this repository does not treat that report as proof of a production-ready character system. Identity fitting, stylized facial parameterization, loose garments, expression systems, physics, and consumer export remain separate qualification gates.

## Repository layout

```text
docs/       durable architecture, policies, acceptance, research history
skills/     thin repeatable execution procedures for agents
schemas/    machine-readable contracts
examples/   small non-sensitive examples
scripts/    deterministic utilities as they are promoted
tests/      mechanical guards and regression tests
fixtures/   synthetic or redistribution-safe test inputs
```

## Public-repository policy

Do not commit credentials, session data, private conversations, personal absolute paths, computer names, raw local logs, or unreviewed production assets. Prefer synthetic fixtures and sanitized evidence summaries.

## Authority

Current user goal > current repo/code/tests/runtime > current official host documentation > durable docs in this repo > historical research/inference.
