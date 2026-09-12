# character-3d-authoring

Use this skill for implementation, repair, or validation work on CharacterKernel character assets.

## Start

1. Read repository `AGENTS.md`.
2. Read the current task/issue/PR and exact local project state.
3. Read only the relevant durable docs:
   - architecture -> `docs/PROCEDURAL_CHARACTER_AUTHORING.md`
   - local edit -> `docs/CHANGE_PROTOCOL.md`
   - pass/fail -> `docs/ACCEPTANCE.md`
   - evidence wording -> `docs/EVIDENCE_MODEL.md`
4. Confirm the Blender/runtime version when behavior is version-sensitive.

## Execute

Use this loop:

```text
OBSERVE
-> identify source_write_set / derived_invalidation_set / protected_source_set
-> make the smallest source edit
-> rebuild affected dependencies or fail closed
-> structural validation
-> visual/locality validation
-> save
-> fresh-process reopen
-> report/re-edit
-> evidence summary
```

## Rules

- Do not redesign the whole kernel during a bounded edit task.
- Do not use generated meshes as canonical topology without an explicit migration decision.
- Do not silently overwrite accepted manual corrections.
- Do not hide garment problems by deleting body source geometry.
- Do not call `VALID` attachment state a visual/deformation PASS.
- Do not claim current runtime behavior from historical research alone.
- If a required dependency cannot be made fresh, stop that path with an explicit unsupported/rebind state and preserve the accepted source.

## Worker delegation

A worker may implement bounded code or Blender changes, but the coordinator/verifier should independently check:

- owned diff;
- runtime behavior;
- structural invariants;
- dependency freshness;
- protected source;
- fresh-process persistence.

## Finish

Leave:

- changed files/source fields;
- exact validation performed;
- unsupported or unverified areas;
- precise resume point.

Promote repeated manual checks into scripts/tests rather than growing prompt text.
