# Change Protocol

## 1. Observe before mutation

Identify:

- exact source/fixture revision;
- current body/topology/semantic/UV/rig revisions;
- active hair/garment components;
- dirty or rebind-required dependencies;
- protected authoring source.

Do not repair a candidate before recording the pre-change state.

## 2. Declare the edit

For every non-trivial edit, declare:

```text
target
source_write_set
derived_invalidation_set
protected_source_set
expected invariants
expected visible effect
rollback/baseline
```

Example — bang length:

```text
source_write_set:
  hair.bangs.guide_params.length

derived_invalidation_set:
  hair.bangs.generated_geometry
  local collision
  preview/export

protected_source_set:
  body
  garment source
  side/back/tail hair source
```

## 3. Apply the smallest source edit

Do not replace a whole character component when a stable local parameter/source exists.

## 4. Rebuild or fail closed

Supported inputs must either:

- rebuild all required dependencies to a validated fresh state; or
- stop with an explicit state such as `REBIND_REQUIRED` / `UNSUPPORTED`.

Never report success with stale derived state.

## 5. Validate at multiple layers

Structural:
- topology/semantic/UV invariants;
- attachment and bind freshness;
- expected revision changes.

Visual:
- intended edit visible;
- obvious hair float, penetration, collapse, or joint breakage absent in declared views.

Locality:
- protected source unchanged;
- derived changes confined to declared dependency closure.

Persistence:
- save;
- fresh process;
- report;
- repeat edit;
- restore accepted state.

## 6. Corruption test

Where feasible, deliberately invalidate one dependency on a copy and confirm the system detects it rather than silently rebuilding from an unintended source.

A corruption test proves only the corruption class actually exercised.

## 7. Evidence

Record exact input/candidate revision, operation, observed result, and verifier scope. Do not treat exit code or self-report alone as PASS.
