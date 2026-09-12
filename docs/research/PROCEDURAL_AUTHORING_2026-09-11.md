# Procedural authoring research — 2026-09-11

Status: historical research input; not current runtime authority.

This note records the direction that informed the initial CharacterKernel architecture after bounded Blender experiments and a focused research pass.

Durable conclusions promoted into the main docs:

- prefer editable source over final-mesh-only delivery;
- keep a stable topology family and separate rest-shape changes from topology identity;
- use surface-relative correspondence for hair/garment/sockets where appropriate;
- re-solve body-specific rig state after identity/body changes;
- treat hair as guides/components plus generated geometry;
- distinguish fitted garments from pattern-parametric/rigid/hybrid representations;
- keep `.blend` authoring state plus machine-readable semantic/report state;
- require fresh-process re-editability;
- include negative/fail-closed dependency tests, not only success-path checks.

Important boundary:

The historical run summaries that motivated these rules were user-reported local host evidence. They are not automatically independent evidence for the current repository implementation.

For current work, use `docs/PROCEDURAL_CHARACTER_AUTHORING.md`, `docs/ACCEPTANCE.md`, and the current code/tests/runtime.

Prior research references were originally collected in the predecessor CodexOperations character-3d work. Re-check current official documentation and licenses before adopting version-sensitive APIs, external models, datasets, or commercial assets.
