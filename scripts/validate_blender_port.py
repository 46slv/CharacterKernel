"""Validate the sanitized Blender proof without importing Blender."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_PROOFS = (
    "public_fixture_builder",
    "separate_authoring_sources",
    "pants_to_body_attachment",
    "belt_to_pants_attachment",
    "supported_deformation_changed_body",
    "supported_deformation_refit_pants",
    "supported_deformation_refit_belt",
    "belt_swap_A_to_B",
    "belt_swap_back_B_to_A",
    "fresh_process_reedit",
    "fresh_process_restore",
    "fresh_process_read_only_verify",
    "source_state_protected",
    "fail_closed_corruption",
    "scene_sensitive_report",
)
PASS_STAGES = ("baseline", "edited", "reedited", "restored", "final_readonly")
FAIL_CLOSED_STAGES = ("corrupt_injection", "corrupt_readonly")
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\|/Users/|/home/)")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(evidence: dict[str, Any], reports: dict[str, dict[str, Any]]) -> None:
    _require(evidence.get("status") == "PASS", "roundtrip evidence is not PASS")
    _require(re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("candidate_revision", ""))) is not None, "candidate revision is not an exact commit")
    _require(evidence.get("runtime", {}).get("blender", "").startswith("5."), "Blender runtime is missing")
    _require(evidence.get("fixture", {}).get("id") == "synthetic_body_pants_belt_v1", "unexpected fixture id")
    proofs = evidence.get("proofs", {})
    for key in REQUIRED_PROOFS:
        _require(proofs.get(key) is True, f"proof is missing or false: {key}")
    _require(evidence.get("protected_invariants", {}).get("core_bpy_free") is True, "core bpy-free invariant is missing")
    _require(evidence.get("protected_invariants", {}).get("source_state_unchanged") is True, "source protection is missing")
    _require(evidence.get("learning_gate", {}).get("status") == "PASS", "learning gate is not PASS")
    _require(evidence.get("learning_gate", {}).get("unsupported_generalization") is True, "fixture workaround was promoted")
    for stage in PASS_STAGES:
        _require(reports.get(stage, {}).get("status") == "PASS", f"stage is not PASS: {stage}")
    for stage in FAIL_CLOSED_STAGES:
        report = reports.get(stage, {})
        _require(report.get("status") == "FAIL", f"corruption stage is not FAIL: {stage}")
        _require(report.get("failure_state") == "REBIND_REQUIRED", f"corruption did not fail closed: {stage}")
    final = reports["final_readonly"]
    _require(final.get("observation", {}).get("read_only") is True, "final report is not read-only")
    _require(final.get("observation", {}).get("mutated") is False, "final report mutated the blend")
    corrupt = reports["corrupt_readonly"]
    _require(corrupt.get("observation", {}).get("mutated") is False, "corruption verify mutated the blend")
    _require(len(evidence.get("processes", [])) >= 7, "fresh-process proof is incomplete")
    serialized = json.dumps(evidence, ensure_ascii=False)
    _require(ABSOLUTE_PATH.search(serialized) is None, "evidence contains an absolute path")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    evidence_path = args.evidence.resolve()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    reports = {}
    for name in (*PASS_STAGES, *FAIL_CLOSED_STAGES):
        report_path = evidence_path.parent / f"report_{name}.json"
        reports[name] = json.loads(report_path.read_text(encoding="utf-8"))
    validate(evidence, reports)
    print(f"evidence={evidence_path.name} stages={len(reports)} status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
