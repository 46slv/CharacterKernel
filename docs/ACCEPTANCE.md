# Acceptance

Acceptance is layered. No single oracle is sufficient.

## Structural gate

For a supported fixed-topology body edit:

- ordered topology unchanged;
- semantic mapping remains compatible;
- UV contract remains compatible or the operation explicitly refuses it;
- evaluated neutral/rest shape changes when the requested edit should change it;
- affected joint/rest-rig/bind state is fresh;
- fitted garment state is fresh;
- affected scalp/hair-root state is fresh;
- protected authoring source remains unchanged.

## Attachment gate

`VALID` means the correspondence contract resolved. It does not by itself prove:

- anatomical correctness;
- collision quality;
- garment clearance;
- hair visual quality;
- deformation quality.

Negative tests should confirm stale/corrupt bindings become explicit fail-closed states such as `REBIND_REQUIRED`.

## Visual gate

Use declared cameras/poses. Check at minimum:

- intended edit is visible;
- no obvious garment penetration in the reviewed views;
- no obvious hair-root float;
- no obvious joint collapse/breakage.

Visual review does not replace structural checks.

## Locality gate

Only declared source fields may change. Derived artifacts may change only inside the expected dependency closure.

## Persistence gate

Required for editable-authoring PASS:

1. save an editable artifact;
2. close the Blender process;
3. open in a fresh process;
4. read a deterministic scene report;
5. repeat representative body/hair/garment edits;
6. confirm editable guides/parameters/references still exist;
7. return to an accepted baseline/state.

## Report gate

A read-only report should:

- read actual scene state;
- return stable semantic payload for the same state;
- not save or alter persistent authoring state;
- distinguish UNKNOWN/UNSUPPORTED from empty/zero;
- change when relevant scene state changes.

Identical JSON twice proves repeatability, not correctness by itself.

## Promotion levels

Suggested labels:

- `DESIGN_ONLY`
- `SCOPED_HOST_PASS`
- `EDITABLE_CORE_READY`
- `IDENTITY_FIT_PASS`
- `FIRST_REUSABLE_CHARACTER`

Do not skip levels by inference.
