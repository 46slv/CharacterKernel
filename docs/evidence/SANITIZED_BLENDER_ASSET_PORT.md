# Sanitized Blender asset-port evidence

Status: `SCOPED_HOST_PASS`

This summary is the public-safe closeout for the synthetic wearable proof. It
contains no private image, mesh, machine path, session data, or raw Blender log.

## Exact candidate and runtime

- Candidate implementation revision: `c5fd67ef320502e284777b45bbd63a0c0bfe770e`
- Contract: `CHARACTERKERNEL_SYNTHETIC_WEARABLE_V1`
- Fixture: `synthetic_body_pants_belt_v1`
- Builder SHA-256: `be9f6dc2fd9e6f1ef329396d9cbda42f78865c09aa689d54a74c08fa16772cd0`
- Blender: `5.2.1 LTS` (`9e2066aef7ef`)
- Bundled Python: `3.13.13`

## Proof result

The deterministic builder produced a 64-vertex / 50-polygon body with 32 pants
attachments and 36 attachments for each belt variant. Pants, belt A, belt B,
and the visible belt result are separate mesh datablocks. The persisted
correspondences use the existing `SurfaceAttachment` contract; no second
attachment representation was introduced.

The seven independent Blender processes were:

```text
build -> edit(width 1.05, A to B) -> re-edit(width 0.96, B to A)
-> restore(width 1.00, A) -> read-only verify
-> corrupt one belt topology revision -> read-only fail-closed verify
```

| Stage | Result | Structural observation |
|---|---|---|
| baseline | `PASS` | body/pants/belt A+B attachments `VALID` |
| edited | `PASS` | body and fitted pants changed; belt B refit and swap changed result |
| reedited | `PASS` | fresh process accepted width 0.96 and swapped back to A |
| restored | `PASS` | baseline body/pants/belt A evaluated hashes returned exactly |
| final read-only | `PASS` | `.blend` SHA before/after equal; `mutated=false` |
| corrupt injection | `FAIL` (expected) | one belt attachment carries a stale topology revision |
| corrupt read-only | `FAIL` (expected) | `failure_state=REBIND_REQUIRED`; `.blend` unchanged |

Baseline structural hashes:

```text
body topology: 71101d053203d2f674554fead8493a21a13975b3bd92f02e56aadea45f8debb4
body semantic:  687e05a2e359e9ee872aa9897d8087dde85dcce2f94fc82145dda19b1720f0ba
body UV:        636ccb2c6df85af70a4fb683432b95681b6c66bfe6e5401ff437f06d16f5c5e5
body rest:      28dbc830bebce52f02799445919756fe981dcb3a8542c2cc741ff4c1606ce3d3
pants fitted:   1351f0f8b443dad11f8ee4e48660b6b2ac599549dfb5f955ac7e9bc9ed59fb50
belt A result:  2e5ff5c97f8e79ac1beb2374214fde31767dc5df3e215250297439228ab17e01
```

The edited state changed body rest to
`28b3efffbd4111fc532adb8e5399ed86a8088161e9e059891294ec28e81c7478`, pants
fit to `93a66b4a2a27a68f473afe5fe1c196db377139b8cba8bd0da90291eaf8fffb06`, and
belt B result to
`96296a94bf7a66b6e15a989f63463883c439d6f4a1a13fa36a77e2a57cb8d863` while
topology, semantic, and UV hashes stayed unchanged. Restore returned all three
baseline hashes above.

Protected source signatures (topology / rest / UV) were:

```text
pants: 6116908a43c93298f4899df1ea8a7b98b237f9e21d8c1b85567b727f383f4d50 /
       0cfd5fddd9e42ba6389e71d69b4072395305e79d1c70430b2959822e485f2e8d /
       479a460a405f04d06722115c4c147e18272827ecc641ef5098f34f5cd9356f56
belt A: f2e57a3022901760182b83117f2d97e5d6abad1109fe1cb74438f7efe3cdba2e /
        f087c1bd70a2a1fcd7e0ac5bb2245b1d0f96058fbb88d4f9f0faa3dfc70d1b81 /
        6ad2ca455cb52aae2703120a8220f5840d368c17c76f86aa7a861b568732c805
belt B: f2e57a3022901760182b83117f2d97e5d6abad1109fe1cb74438f7efe3cdba2e /
        4a98d131f78593fdadcbaeb6d8547236647e6bcfd8cfd135b9d3eab0c60c44f7 /
        6ad2ca455cb52aae2703120a8220f5840d368c17c76f86aa7a861b568732c805
```

All three source signatures matched the baseline in every edit, swap, restore,
and read-only report.

## Learning Gate

`PASS` for this bounded capability. The basis-relative lower-body depth
shape-key pair is retained as a synthetic-fixture probe only. It is not promoted
to a general body-fitting or identity-fitting rule. The public implementation
reuses the current attachment, hashing, dependency, and fail-closed primitives;
the only new pure contract is immutable wearable variant selection plus batch
attachment validation.

## Unsupported and resume point

Identity fitting, private `ss` assets, final 私服001 design, full cloth or sewing
patterns, expressions, tracking, consumer export, and production visual quality
are not proven here.

Re-run from the task branch with the documented command in `README.md`; the
fresh-process checkpoint is `evidence/local/blender_asset_port/` (ignored local
evidence), and the next structural entry point is
`scripts/blender_asset_proof.py --mode verify` against `candidate_final.blend`.
