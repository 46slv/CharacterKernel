# Evidence Model

## Evidence classes

| Class | Meaning | Does not imply |
|---|---|---|
| `SPEC_VERIFIED` | A specific primary-source statement was checked for a stated version/date | Local implementation or host PASS |
| `USER_REPORTED_HOST_EVIDENCE` | A user supplied a local execution result | Independent reproduction |
| `INDEPENDENT_HOST_EVIDENCE` | A verifier independently inspected/re-ran the relevant artifact | Production generality |
| `DESIGN_INFERENCE` | A design decision inferred from requirements and evidence | Host truth or optimality |
| `PROPOSED_CAPABILITY` | A proposed operation/schema/tool surface | Implemented API |
| `HISTORICAL_NOT_REVERIFIED` | Prior research retained for context | Current provider/license/API truth |

## Required evidence tuple

Strong claims should bind:

```text
requirement
+ exact input
+ source/candidate revision
+ runtime/version
+ actual operation
+ observed result
+ protected-state comparison
+ verifier scope
```

Avoid combining PASS results from different candidates as if one candidate satisfied all gates.

## Common overclaims to reject

- `137/137 VALID` does not mean 137 distinct corruption classes were tested.
- Identical report hashes do not prove report values are correct.
- Unchanged `.blend` bytes do not prove no transient in-memory mutation occurred.
- Six renders do not prove all six passed visual review unless those images were actually reviewed.
- A topology-preserving edit does not prove deformation quality.
- A generated turnaround is not original-reference truth.

## Provenance priority

Current user-confirmed source/reference > direct visible source evidence > explicitly generated hypotheses > generator-only hidden detail.

Generated references should carry provenance and uncertainty rather than silently becoming source truth.
