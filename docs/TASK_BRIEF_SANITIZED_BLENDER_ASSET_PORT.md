# Task Brief — Sanitized Blender Asset Port

Status: `READY_FOR_LUNA_MAX_EXECUTION`

Target repository: `46slv/CharacterKernel`
Base branch: `feature/core-runtime-scaffold`
Base head at brief authoring: `a239083fea2029640baba3096b7393fe6e94a354`
Task branch: `task/sanitized-blender-asset-port`

## Goal

Port the reusable structural capability proven in the private Luna Max pants/belt trial into CharacterKernel as a public-safe, Blender-backed asset/attachment capability.

The port must prove that reusable assets can remain separate authoring sources while a belt-like wearable is attached to a pants/body target, refit after supported deformation, swapped for another compatible asset, saved, reopened in a fresh Blender process, re-edited, restored, and verified without corrupting protected source state.

This task is a structural port. It is not an `ss` visual-production task.

## User-visible outcome

After this task, CharacterKernel should contain one small redistribution-safe Blender proof showing the reusable pattern:

```text
body/kernel fixture
  + pants-like target asset
      + semantic waistband / attachment target
  + belt asset A
  + belt asset B
  + persisted attachment / fit contract
      -> refit after supported deformation
      -> swap A/B
      -> fresh-process re-edit
      -> restore
```

The useful product is not the demo mesh itself. The useful product is the public, testable asset + attachment/refit/swap contract and the smallest Blender adapter needed to exercise it.

## Authority / read order

Use current sources in this order:

1. current user instruction and this task brief;
2. live `AGENTS.md`, current code/tests/fixtures and actual Blender runtime evidence;
3. `docs/PORTING_EDITABLE_CORE.md`;
4. `docs/PROCEDURAL_CHARACTER_AUTHORING.md`, `docs/ARCHITECTURE.md`, `docs/CHANGE_PROTOCOL.md`, `docs/ACCEPTANCE.md`, `docs/EVIDENCE_MODEL.md` as needed;
5. current official Blender documentation for version-sensitive behavior;
6. historical/local trial evidence as migration input only.

Do not treat a report summary as a substitute for inspecting the exact local prototype when that prototype is available to the run.

## Starting point

The current public branch already provides host-independent primitives:

- revision-aware `SurfaceAttachment` evaluation;
- barycentric-triangle and weighted-vertex-set correspondence;
- fail-closed `REBIND_REQUIRED`;
- dependency freshness / invalidation closure;
- deterministic semantic hashing;
- schemas/examples/contract validation;
- 13 focused unit tests reported PASS before this task.

The private bounded trial subsequently reported a successful Blender 5.2.1 structural proof using separate pants and belt A/B fixtures, refit, swap, fresh-process re-edit, restore and read-only verification across five independent Blender processes. Sol/Astra and human intervention were not required.

That private result is prior evidence, not public CharacterKernel parity. This task must independently reproduce the reusable behavior with redistribution-safe inputs.

The exact local trial workspace/artifacts are supplied out-of-band at execution time. Do not commit personal absolute paths, machine names, raw logs, private images or provider/session data into this public repository.

## Required preflight

Before implementation:

1. Confirm the actual task branch/revision and existing uncommitted state.
2. Read the current repo routing/docs above.
3. Inspect the exact local trial implementation and evidence in its original workspace if accessible.
4. Record source hashes/runtime/version locally for provenance.
5. Identify what is genuinely reusable versus fixture-specific.
6. Determine the narrowest Blender adapter boundary that keeps host-independent correspondence/hash/dependency logic free of `bpy` state access.
7. Decide whether the redistribution-safe fixture should be committed as generated source + deterministic builder, a small reviewed `.blend`, or both. Prefer generated/reproducible source when practical.

Do not begin by designing a new all-purpose garment framework.

## Requirements

### R1 — Public-safe synthetic fixture

Create a redistribution-safe fixture representing at least:

- one body/kernel-compatible target;
- one pants-like asset or target surface;
- one stable semantic waistband / belt attachment target;
- two interchangeable belt-like assets A/B.

The fixture must not contain private `ss` images, private meshes, personal paths, machine-specific secrets or unclear-license production assets.

### R2 — Separate authoring sources

Pants/body source and belt A/B source must remain separately editable. The fitted result must not become the only authoritative copy of a belt.

PASS example: changing/replacing belt source can rebuild the fitted belt without remodeling the pants.

FAIL example: the only surviving belt is a destructively-applied mesh whose original source/parameters cannot be recovered.

### R3 — Persisted attachment / fit contract

The relationship between belt and target must be represented by durable semantic/surface correspondence, not only by current world-space XYZ.

Reuse current `SurfaceAttachment` or extend it only when real evidence proves the current representation insufficient. Do not silently fork a second attachment system.

### R4 — Supported deformation refit

Apply at least one controlled supported deformation that changes the evaluated target shape while preserving the declared topology/semantic/UV contract. Recompute/refit the belt through declared dependency closure.

Acceptance must distinguish source geometry identity from evaluated/rest shape where Shape Keys or equivalent evaluated deformation are used.

### R5 — Swap

Swap belt A -> B -> A without rewriting unrelated pants/body authoring source.

Protected non-target source state must remain unchanged except for declared downstream derived state/revisions.

### R6 — Restore

Return the supported deformation and wearable selection to baseline and prove the baseline semantic/evaluated state is restored according to declared hashes/measurements.

Do not use revision-number changes alone as proof of geometric change or restoration.

### R7 — Fail-closed corruption

Deliberately invalidate at least one attachment-relevant contract and prove stale success is rejected, preferably through the existing `REBIND_REQUIRED` path or a compatible explicit fail-closed state.

The corruption test must not permanently damage the protected fixture/source.

### R8 — Read-only verification

Provide or extend a read-only report/verification path that:

- reads actual scene state;
- is sensitive to real supported scene changes;
- distinguishes stable semantic payload from observation metadata/timestamps;
- does not save, rebind, clean up, alter parameters or mutate authoring source;
- can demonstrate persistent non-mutation using file/source signatures where practical.

Two identical reports alone are not sufficient; also demonstrate sensitivity to at least one intentional supported state change.

### R9 — Fresh-process roundtrip

Use independent Blender processes to prove at minimum:

```text
create/baseline
-> edit/refit
-> save
-> close
-> fresh process reopen
-> read-only verify
-> re-edit or swap
-> save/reopen as needed
-> restore
-> final verify
```

An in-memory-only pass is not sufficient.

### R10 — Existing invariants remain protected

At minimum verify, where applicable:

- topology identity preserved;
- semantic mapping preserved;
- UV contract preserved;
- host-independent core stays `bpy`-free;
- attachment revision checks still fail closed;
- private/public repository guard passes.

### R11 — Tests and deterministic validation

All pre-existing tests must still pass.

Add focused tests/validators for new reusable behavior where it can be mechanized. Prefer deterministic assertions over screenshots for structural claims.

Visual review may supplement but must not replace structural/persistence evidence.

### R12 — Evidence and Learning Gate

Tie claims to exact repository revision, fixture/source hash, Blender version, command/operation and observed result.

Run the project/operations Mandatory Learning Gate before reporting Done. A fixture-specific workaround must not be promoted to a general rule without sufficient evidence.

## Important unknowns to resolve early

1. Whether the private trial's Basis-relative y-only repair is a reusable pattern or fixture-specific workaround.
2. Whether current `SurfaceAttachment` fields are sufficient for the wearable target without schema change.
3. Whether target deformation should be expressed through Shape Keys, a controlled deformer, or another minimal mechanism in the public fixture.
4. Whether the best public fixture form is a checked-in synthetic `.blend`, a deterministic Blender Python builder, or builder + generated evidence.
5. Whether read-only scene reporting needs a Blender adapter extension or can reuse current host-independent semantic hashing plus a narrow state extractor.

These are probe targets, not reasons to redesign the whole kernel.

## Non-goals

Do not add during this task unless directly required to satisfy the above proof:

- `ss` identity fitting or any private character asset;
- final 私服001 visual design;
- stylized/anime face solving;
- full garment sewing-pattern system;
- cloth simulation framework;
- expressions;
- hair production system;
- VRM/glTF/FBX consumer delivery;
- tracking/streaming runtime;
- a new operator framework, orchestration framework or generic asset manager;
- a complete Blender Asset Library product/UI.

## Execution topology

Primary owner: **Luna Max**.

Continue with Luna while evidence is improving. A large task is not itself an escalation reason.

Bounded upper-model advice is allowed only when the task meets the previously established escalation conditions:

- same failure fingerprint survives materially different reasonable approaches;
- architecture/source-of-truth ambiguity remains after focused probes;
- cross-layer root cause remains unresolved;
- the acceptance oracle itself is materially ambiguous;
- irreversible/publication/authority boundary requires judgment.

For this structural/public-safe task, prefer **Sol** for architecture/oracle diagnosis. Astra should normally be unnecessary because visual identity is explicitly out of scope. If a higher-model directive is obtained, persist the decision/evidence and return implementation ownership to Luna Max.

## Suggested phases

### P0 — Inspect and map

- inspect local trial artifacts/evidence;
- map private trial mechanisms to existing CharacterKernel core;
- classify reusable vs fixture-specific behavior;
- choose the minimal public fixture/adapter plan.

### P1 — Public fixture

- implement deterministic synthetic fixture/builder;
- establish stable semantic target and belt A/B authoring sources;
- prove baseline structural report.

### P2 — Attachment/refit/swap

- bind/attach through existing contracts;
- supported deformation -> recompute/refit;
- A/B swap;
- restore;
- non-target-state protection.

### P3 — Negative and persistence proof

- deliberate invalidation -> fail closed;
- independent-process save/reopen/re-edit/restore;
- repeated read-only report with mutation sensitivity and disk/source protection.

### P4 — Tests/docs/evidence

- run existing + new tests;
- run contract validation;
- update `PORTING_EDITABLE_CORE.md` parity status without overstating scope;
- record exact evidence and unsupported cases;
- run Mandatory Learning Gate;
- prepare Draft PR evidence.

## Done

This task is Done only when all of the following are true:

1. Public-safe implementation exists on the task branch.
2. A redistribution-safe Blender fixture or deterministic fixture builder exists.
3. Pants/target + belt A/B remain separate editable authoring sources.
4. Attachment/refit after supported deformation is demonstrated.
5. A/B swap and baseline restore are demonstrated.
6. A deliberate stale/corrupt attachment fails closed.
7. Read-only reporting is both non-mutating and scene-sensitive.
8. Fresh-process reopen/re-edit/restore succeeds.
9. Declared topology/semantic/UV/protected-source invariants pass.
10. Existing 13 tests plus all new focused tests/validators pass, or current live test-count equivalent is reported exactly if the suite has changed.
11. No private/sensitive/non-redistributable data is committed.
12. Evidence is tied to exact candidate revision and runtime.
13. Remaining unsupported behavior is explicit.
14. Mandatory Learning Gate result is recorded.
15. A Draft PR is opened or updated; merge is not part of this task unless separately authorized.

## False-Done examples

Do **not** report Done if any of these is true:

- Blender opened the file but no fresh-process re-edit was demonstrated;
- belt visually follows once, but correspondence is not durable after deformation/reopen;
- swap works only by destructively rebuilding pants/body source;
- only screenshots or self-report support structural claims;
- repeated JSON hashes are used as the sole proof of correctness;
- topology/UV/semantic preservation is assumed rather than checked;
- private trial assets/paths/logs were copied into the public repository;
- existing unit tests pass but the Blender parity fixture was not actually exercised;
- the generic mechanism was replaced by an `ss`-specific hardcoded solution.

## Stop / checkpoint conditions

Do not stop for ordinary implementation ambiguity if a bounded probe can resolve it.

Checkpoint and escalate only when:

- a consequential schema/topology migration appears necessary;
- a repeated failure fingerprint no longer yields new evidence;
- Blender capability/version behavior prevents the acceptance proof after direct runtime probing;
- the local private prototype is required but inaccessible and reconstruction from reports would risk inventing behavior;
- publication would require copying private or unclear-license material;
- acceptance would need to be weakened.

A blocked checkpoint must contain:

```text
STATUS
CURRENT REVISION
DONE CHECKS
FAILING CHECKS
FAILURE FINGERPRINT
WHAT WAS TRIED
EVIDENCE
SURVIVING HYPOTHESES
DECISION NEEDED
SAFE NEXT ACTION
EXACT RESUME POINT
```

## Final report shape

Return a compact completion report containing:

```text
STATUS
CANDIDATE REVISION / PR
BLENDER VERSION
IMPLEMENTED CAPABILITY
TEST / VALIDATION RESULTS
FRESH-PROCESS EVIDENCE
PROTECTED INVARIANTS
FAIL-CLOSED EVIDENCE
REUSABLE DELTA / LEARNING GATE
UPPER-MODEL ESCALATIONS (if any)
UNSUPPORTED / NOT PROVEN
NEXT BEST ACTION
EXACT RESUME POINT
```

The likely next gate after a successful sanitized port is a **fresh private `ss / 私服001` identity/design production run**, where Astra can spend its effort on real visual interpretation instead of re-solving this structural mechanism.
