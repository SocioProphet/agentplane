#!/usr/bin/env python3
"""Epistemic-hygiene runtime — the live, teeth-verified layer.

Turns the standard-rich / runtime-poor epistemic-hygiene layer into a standing
producer. This is the follow-up item 1 named in the Crown constitution
(hellgraph#52, docs/adr/0004-crown-telos-truth-constitution.md): "Hygiene runtime
is standard-rich / runtime-poor … no CTEST runner, no bias-passport /
calibration-passport producer … id-namespace drift."

Seats under the Crown (bind-upward):

  | Constitutional role (ADR-0004)                 | Realized here                          |
  | ---------------------------------------------- | -------------------------------------- |
  | Truth Engine's Test-Obligation (T1)            | run_ctest() — a claim with no          |
  |   "no Test-Obligation -> void"                 |   counter-test/falsifier -> verdict    |
  |                                                |   epistemically_void (mirrors the      |
  |                                                |   SILENT Phase-0 gate, eik#2)          |
  | D1 "Da'at cannot assert truth" =               | run_ctest() rejects an affirming-the-  |
  |   affirming-the-consequent guard (eik#3)       |   consequent inference with            |
  |                                                |   REJECTED_AFFIRMING_THE_CONSEQUENT     |
  | Bias/Calibration Passport feeding Truth Record | produce_bias_passport() /              |
  |                                                | produce_calibration_passport()          |

Consume-not-fork: the governed detector-id map + bias catalog are authored in
SocioProphet/sociosphere; a byte-copy projection is vendored at
tools/epigov/detector-id-map.vendored.json (teeth for the map itself live in
sociosphere CI — validate_detector_id_map.py). This runtime ENFORCES the map:
any detector id not present as a governed standard id is REJECTED before a
passport is emitted.

Deterministic + stdlib (json, hashlib, argparse, pathlib) + jsonschema for
artifact conformance. Same input + same ruleset hash -> byte-identical output.
Artifacts conform to schemas/hygiene-run-artifact.schema.json and
schemas/countertest-run-artifact.schema.json and are sealed with a
proof-artifact-spine SHA-256 receipt (canonical JSON + entryHash).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDORED = Path(__file__).resolve().parent / "epigov" / "detector-id-map.vendored.json"
HYGIENE_SCHEMA_PATH = ROOT / "schemas" / "hygiene-run-artifact.schema.json"
COUNTERTEST_SCHEMA_PATH = ROOT / "schemas" / "countertest-run-artifact.schema.json"

PROTOCOL_REF = "protocol/epistemic-governance/v1"
# Deterministic timestamp for reproducible example artifacts / selftest.
FIXED_ISSUED_AT = "2026-08-03T00:00:00Z"


# ─── errors ──────────────────────────────────────────────────────────────────
class HygieneRuntimeError(Exception):
    """Raised when a passport/runner input violates a governed invariant."""


# ─── canonical hashing + proof-artifact-spine seal ───────────────────────────
def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_of(obj) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def seal(artifact: dict, ledger_seq: int = 0, ledger_prev_hash: str | None = None) -> dict:
    """Emit a proof-artifact-spine receipt over an artifact.

    Mirrors prophet-workspace tools/proof-artifact-spine (canonical JSON + sha256
    + ledgerPrevHash + ledgerSeq + entryHash). Fail-closed: a producer that
    cannot seal has not produced.
    """
    record = {
        "recordType": artifact["kind"] + "Receipt",
        "ledgerSeq": ledger_seq,
        "ledgerPrevHash": ledger_prev_hash or "sha256:" + "0" * 64,
        "artifactId": artifact["artifact_id"],
        "inputHash": artifact["input_hash"],
        "outputHash": sha256_of(artifact),
        "emittedAt": artifact["issued_at"],
    }
    record["entryHash"] = sha256_of(record)
    return record


def verify_seal(artifact: dict, receipt: dict) -> bool:
    if receipt.get("outputHash") != sha256_of(artifact):
        return False
    probe = {k: v for k, v in receipt.items() if k != "entryHash"}
    return receipt.get("entryHash") == sha256_of(probe)


# ─── governed namespace (vendored, enforced) ─────────────────────────────────
class Namespace:
    def __init__(self, vendored: dict):
        self._v = vendored
        self.emitted_to_standard = {
            e["emitted_id"]: e["standard_id"] for e in vendored["detector_id_map"]
        }
        self.succeeds_into = {
            e["standard_id"]: e.get("succeeds_into") for e in vendored["detector_id_map"]
        }
        self.standard_ids = set(self.emitted_to_standard.values())
        bc = vendored["bias_catalog"]
        self.bias_to_id = {b["key"]: b["detector_id"] for b in bc["biases"]}
        self.bias_ct = {b["key"]: b["required_counter_test"] for b in bc["biases"]}
        self.tooth = bc["formal_validity_tooth"]
        ctm = vendored["counter_test_map"]
        self.required_cts = ctm["required_counter_tests"]
        self.runnable_ct = set(ctm["runnable"])
        self.proposed_ct = set(ctm["proposed"])
        # A governed id is any id the standard declares (map standard ids, all
        # ids named by the bias catalog, plus every detector the ruleset lists a
        # required-counter-test for — i.e. the whole declared detector surface).
        self.governed_ids = (
            self.standard_ids
            | set(self.bias_to_id.values())
            | {self.tooth["detector_id"]}
            | set(self.required_cts.keys())
        )
        self.ruleset_hash = vendored["_provenance"]["ruleset_sha256"]

    @classmethod
    def load(cls, path: Path = VENDORED) -> "Namespace":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def reconcile(self, emitted_id: str) -> str:
        """Map a runtime-emitted id to its governed standard id, or REJECT."""
        std = self.emitted_to_standard.get(emitted_id)
        if std is None:
            raise HygieneRuntimeError(
                f"detector id {emitted_id!r} is not in the governed id map "
                f"(unmapped / drifted) -> REJECTED"
            )
        return std

    def require_governed(self, detector_id: str) -> str:
        """Assert a detector id is a governed standard id, or REJECT."""
        if detector_id not in self.governed_ids:
            raise HygieneRuntimeError(
                f"detector id {detector_id!r} is not a governed standard id -> REJECTED"
            )
        return detector_id

    def bias_detector_id(self, bias_key: str) -> str:
        did = self.bias_to_id.get(bias_key)
        if did is None:
            raise HygieneRuntimeError(
                f"bias key {bias_key!r} is not in the governed set-1 catalog -> REJECTED"
            )
        return did


# ─── schema validation ───────────────────────────────────────────────────────
def _validator(schema_path: Path):
    import jsonschema  # required; CI installs it

    return jsonschema.Draft202012Validator(json.loads(schema_path.read_text()))


def validate_artifact(artifact: dict) -> list[str]:
    kind = artifact.get("kind")
    if kind == "HygieneRunArtifact":
        v = _validator(HYGIENE_SCHEMA_PATH)
    elif kind == "CountertestRunArtifact":
        v = _validator(COUNTERTEST_SCHEMA_PATH)
    else:
        return [f"unknown artifact kind {kind!r}"]
    errs = [e.message for e in v.iter_errors(artifact)]
    if artifact.get("sociosphere_protocol_ref") != PROTOCOL_REF:
        errs.append(f"sociosphere_protocol_ref must be {PROTOCOL_REF!r}")
    return errs


# ─── producers ───────────────────────────────────────────────────────────────
def produce_bias_passport(
    ns: Namespace, detections: list[dict], *, run_id: str, issued_at: str = FIXED_ISSUED_AT
) -> dict:
    """Emit a HygieneRunArtifact (Bias Passport).

    Each detection must carry a governed detector id — either directly
    (`detector_id`) or via a set-1 `bias_key`. A detection that resolves to no
    governed id is REJECTED before emission (teeth).
    """
    findings = []
    for i, d in enumerate(detections):
        if d.get("bias_key"):
            did = ns.bias_detector_id(d["bias_key"])
        elif d.get("detector_id"):
            did = ns.require_governed(d["detector_id"])
        else:
            raise HygieneRuntimeError(
                f"detection[{i}] carries neither bias_key nor detector_id — "
                f"a bias detection without a governed id is REJECTED"
            )
        findings.append({
            "finding_id": f"{run_id}_bias_{i:03d}",
            "claim_ref": d["claim_ref"],
            "finding_type": "cognitive_bias" if did.startswith("COGBIAS.") else "logical_fallacy",
            "finding_detector_id": did,
            "severity": d.get("severity", "warning"),
            "description": d.get("description", ""),
        })
    top_detector = findings[0]["finding_detector_id"] if findings else "COGBIAS.CONFIRM.V1"
    input_obj = {"profile": "bias-passport", "run_id": run_id, "detections": detections}
    artifact = {
        "kind": "HygieneRunArtifact",
        "artifact_id": f"{run_id}_bias_passport",
        "run_ref": f"agentplane://run/epigov-hygiene-runtime/{run_id}",
        "detector_id": top_detector,
        "hygiene_profile": "bias-passport",
        "ruleset_hash": ns.ruleset_hash,
        "input_hash": sha256_of(input_obj),
        "claims_evaluated": len({d["claim_ref"] for d in detections}),
        "hygiene_findings": findings,
        "validation_artifact_ref": f"agentplane://validation/epigov-hygiene-runtime/{run_id}",
        "replay_artifact_ref": f"agentplane://replay/epigov-hygiene-runtime/{run_id}",
        "sociosphere_protocol_ref": PROTOCOL_REF,
        "replay_verified": True,
        "issued_at": issued_at,
    }
    errs = validate_artifact(artifact)
    if errs:
        raise HygieneRuntimeError(f"produced Bias Passport is not schema-conformant: {errs}")
    return artifact


def produce_calibration_passport(
    ns: Namespace, calibration_state: dict, *, run_id: str,
    detections: list[dict] | None = None, issued_at: str = FIXED_ISSUED_AT
) -> dict:
    """Emit a HygieneRunArtifact (Calibration Passport) carrying drift state."""
    detections = detections or []
    findings = []
    for i, d in enumerate(detections):
        did = ns.require_governed(d["detector_id"])
        findings.append({
            "finding_id": f"{run_id}_calib_{i:03d}",
            "claim_ref": d["claim_ref"],
            "finding_type": "cognitive_bias",
            "finding_detector_id": did,
            "severity": d.get("severity", "info"),
            "description": d.get("description", ""),
        })
    input_obj = {"profile": "calibration-passport", "run_id": run_id,
                 "calibration_state": calibration_state, "detections": detections}
    artifact = {
        "kind": "HygieneRunArtifact",
        "artifact_id": f"{run_id}_calibration_passport",
        "run_ref": f"agentplane://run/epigov-hygiene-runtime/{run_id}",
        "detector_id": findings[0]["finding_detector_id"] if findings else "COGBIAS.OVERCONF.V1",
        "hygiene_profile": "calibration-passport",
        "calibration_state": calibration_state,
        "ruleset_hash": ns.ruleset_hash,
        "input_hash": sha256_of(input_obj),
        "claims_evaluated": len({d["claim_ref"] for d in detections}),
        "hygiene_findings": findings,
        "validation_artifact_ref": f"agentplane://validation/epigov-hygiene-runtime/{run_id}",
        "replay_artifact_ref": f"agentplane://replay/epigov-hygiene-runtime/{run_id}",
        "sociosphere_protocol_ref": PROTOCOL_REF,
        "replay_verified": True,
        "issued_at": issued_at,
    }
    errs = validate_artifact(artifact)
    if errs:
        raise HygieneRuntimeError(f"produced Calibration Passport is not schema-conformant: {errs}")
    return artifact


# ─── CTEST runner (Test-Obligation, T1 / SILENT Phase-0) ─────────────────────
_VALID_FORMS = {"modus_ponens", "modus_tollens"}
_INVALID_FORMS = {"affirm_consequent", "deny_antecedent"}


def _operative_ctest(ns: Namespace, claim: dict) -> str | None:
    if claim.get("counter_test"):
        return claim["counter_test"]
    std = claim.get("detector_id")
    reqs = ns.required_cts.get(std) if std else None
    return reqs[0] if reqs else None


def run_ctest(ns: Namespace, hygiene_run_ref: str, claims: list[dict], *,
              run_id: str, issued_at: str = FIXED_ISSUED_AT) -> dict:
    """Run counter-tests over claims; produce a CountertestRunArtifact.

    Per claim:
      * no falsifier / no counter-test obligation -> epistemically_void (T1).
      * affirming-the-consequent (or denying-the-antecedent) inference used to
        assert a verdict -> confirmed_finding + REJECTED_AFFIRMING_THE_CONSEQUENT
        (Crown D1 / SILENT firewall eik#3).
      * a counter-test that PASSES (claim withstands) -> refuted_finding (admit).
      * a counter-test that refutes the claim -> confirmed_finding.
    """
    outcomes = []
    operative = None
    for i, claim in enumerate(claims):
        oid = f"{run_id}_ctest_{i:03d}"
        finding_ref = claim.get("finding_ref", claim.get("claim_id", f"claim_{i}"))
        ct = _operative_ctest(ns, claim)
        if operative is None and ct:
            operative = ct

        # T1 / Phase-0: unfalsifiable -> void
        if not claim.get("falsifier") or ct is None:
            outcomes.append({
                "outcome_id": oid, "finding_ref": finding_ref,
                "verdict": "epistemically_void",
                "steelman_claim": ("No observation could refute this claim (no declared "
                                   "falsifier / no counter-test obligation); withheld from the "
                                   "testable set — Crown T1 / SILENT Phase-0 gate."),
            })
            continue

        form = claim.get("inference_form")
        if form in _INVALID_FORMS:
            code = "REJECTED_AFFIRMING_THE_CONSEQUENT"
            outcomes.append({
                "outcome_id": oid, "finding_ref": finding_ref,
                "verdict": "confirmed_finding",
                "rejection_code": code,
                "steelman_claim": ("Even under the most charitable reading, inferring the "
                                   "antecedent from the consequent is formally invalid; a "
                                   "verdict manufactured this way is void (Crown D1 = SILENT "
                                   "firewall affirming-the-consequent guard, eik#3)."),
            })
            continue

        # counter-test evaluation (deterministic)
        refuted = bool(claim.get("counter_test_refutes"))
        if form in _VALID_FORMS and not refuted:
            outcomes.append({
                "outcome_id": oid, "finding_ref": finding_ref,
                "verdict": "refuted_finding",
                "steelman_claim": ("The claim's inference is formally valid and withstands the "
                                   "strongest counter-claim; the hygiene finding is overturned "
                                   "and the claim is admitted."),
                "counter_evidence_refs": claim.get("counter_evidence_refs", []),
            })
        elif refuted:
            outcomes.append({
                "outcome_id": oid, "finding_ref": finding_ref,
                "verdict": "confirmed_finding",
                "steelman_claim": ("The strongest counter-claim survives scrutiny; the hygiene "
                                   "finding stands."),
                "counter_evidence_refs": claim.get("counter_evidence_refs", []),
            })
        else:
            outcomes.append({
                "outcome_id": oid, "finding_ref": finding_ref,
                "verdict": "refuted_finding",
                "steelman_claim": ("A concrete falsifier is declared and the counter-test does "
                                   "not refute it; the finding is overturned and the claim is "
                                   "admitted."),
                "counter_evidence_refs": claim.get("counter_evidence_refs", []),
            })

    input_obj = {"hygiene_run_ref": hygiene_run_ref, "run_id": run_id, "claims": claims}
    artifact = {
        "kind": "CountertestRunArtifact",
        "artifact_id": f"{run_id}_countertest_run",
        "run_ref": f"agentplane://run/epigov-hygiene-runtime/{run_id}",
        "countertest_id": operative or "CTEST.FORMAL-VALIDITY.V1",
        "hygiene_run_ref": hygiene_run_ref,
        "input_hash": sha256_of(input_obj),
        "ruleset_hash": ns.ruleset_hash,
        "findings_addressed": len(outcomes),
        "countertest_outcomes": outcomes,
        "validation_artifact_ref": f"agentplane://validation/epigov-hygiene-runtime/{run_id}",
        "replay_artifact_ref": f"agentplane://replay/epigov-hygiene-runtime/{run_id}",
        "sociosphere_protocol_ref": PROTOCOL_REF,
        "replay_verified": True,
        "issued_at": issued_at,
    }
    errs = validate_artifact(artifact)
    if errs:
        raise HygieneRuntimeError(f"produced CountertestRunArtifact is not schema-conformant: {errs}")
    return artifact


# ─── example emission ────────────────────────────────────────────────────────
def _example_detections() -> list[dict]:
    return [
        {"bias_key": "confirmation", "claim_ref": "claim://epigov/demo/claim_001",
         "severity": "warning",
         "description": "Only supporting sources cited; disconfirming evidence not sought."},
        {"bias_key": "framing", "claim_ref": "claim://epigov/demo/claim_002",
         "severity": "info",
         "description": "Gain-framed and loss-framed statements reach opposite conclusions."},
    ]


def _example_claims(hygiene_run_ref: str) -> list[dict]:
    return [
        # withstands -> admitted
        {"claim_id": "claim_001", "finding_ref": "demo_bias_000",
         "detector_id": "COGBIAS.CONFIRM.V1", "counter_test": "CTEST.DEVIL-S.LIST.V1",
         "falsifier": "a disconfirming source that survives review",
         "inference_form": "modus_ponens", "counter_test_refutes": False},
        # unfalsifiable -> void (T1)
        {"claim_id": "claim_002", "finding_ref": "demo_bias_001",
         "detector_id": "COGBIAS.FRAMING.V1", "falsifier": None},
        # affirming the consequent -> confirmed + D1
        {"claim_id": "claim_003", "finding_ref": "demo_afc_000",
         "detector_id": "LOGFALL.AFFIRMCONSEQ.V1", "counter_test": "CTEST.FORMAL-VALIDITY.V1",
         "falsifier": "an alternative antecedent that yields the same consequent",
         "inference_form": "affirm_consequent"},
    ]


def emit_examples(ns: Namespace, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    bias = produce_bias_passport(ns, _example_detections(), run_id="demo")
    calib = produce_calibration_passport(
        ns, {"metric": "reasoning_calibration", "brier_score": 0.12,
             "drift": "within_tolerance", "n": 42}, run_id="demo")
    ctest = run_ctest(ns, bias["run_ref"], _example_claims(bias["run_ref"]), run_id="demo")
    for name, art in [("bias-passport", bias), ("calibration-passport", calib),
                      ("countertest-run", ctest)]:
        (out_dir / f"{name}.example.json").write_text(json.dumps(art, indent=2) + "\n")
        (out_dir / f"{name}.receipt.json").write_text(json.dumps(seal(art), indent=2) + "\n")
    print(f"wrote example artifacts + receipts to {out_dir}")


# ─── selftest (teeth both ways) ──────────────────────────────────────────────
def selftest(ns: Namespace) -> int:
    checks: list[tuple[str, bool]] = []

    def check(label: str, cond: bool):
        checks.append((label, bool(cond)))

    # 1) id-map enforcement — both directions
    check("id-map: emitted->standard reconciles",
          ns.reconcile("LOGFALL.ADHOMINEM.V1") == "LOGFALL.ADHOMINEM.V1")
    try:
        ns.reconcile("LOGFALL.NOTREAL.V9"); check("id-map: drifted id REJECTED", False)
    except HygieneRuntimeError:
        check("id-map: drifted id REJECTED", True)

    # 2) set-1 catalog: each bias resolves to a governed id
    set1 = ["confirmation", "fundamental_attribution_error", "hindsight", "framing", "belief_bias"]
    check("set-1: all five biases resolve to governed ids",
          all(ns.bias_detector_id(k) in ns.governed_ids for k in set1))
    check("D1 tooth is governed (affirming-the-consequent)",
          ns.tooth["detector_id"] in ns.governed_ids and ns.tooth["crown_invariant"] == "D1")

    # 3) Bias Passport — produced conforms + seal verifies
    bias = produce_bias_passport(ns, _example_detections(), run_id="st")
    check("bias-passport: schema-conformant + sealed",
          not validate_artifact(bias) and verify_seal(bias, seal(bias)))
    check("bias-passport: every finding carries a governed detector id",
          all(f["finding_detector_id"] in ns.governed_ids for f in bias["hygiene_findings"]))
    # a bias detection lacking a governed id is REJECTED
    try:
        produce_bias_passport(ns, [{"claim_ref": "c", "detector_id": "COGBIAS.MADEUP.V1"}], run_id="st")
        check("bias-passport: ungoverned detection REJECTED", False)
    except HygieneRuntimeError:
        check("bias-passport: ungoverned detection REJECTED", True)
    try:
        produce_bias_passport(ns, [{"claim_ref": "c"}], run_id="st")
        check("bias-passport: id-less detection REJECTED", False)
    except HygieneRuntimeError:
        check("bias-passport: id-less detection REJECTED", True)

    # 4) Calibration Passport
    calib = produce_calibration_passport(ns, {"brier_score": 0.1, "drift": "within_tolerance"}, run_id="st")
    check("calibration-passport: schema-conformant + sealed + carries state",
          not validate_artifact(calib) and verify_seal(calib, seal(calib))
          and calib["hygiene_profile"] == "calibration-passport" and "calibration_state" in calib)

    # 5) CTEST runner — void, admit, D1, and non-conformance
    ct = run_ctest(ns, bias["run_ref"], _example_claims(bias["run_ref"]), run_id="st")
    verdicts = [o["verdict"] for o in ct["countertest_outcomes"]]
    check("ctest: unfalsifiable claim -> epistemically_void (T1)", "epistemically_void" in verdicts)
    check("ctest: passing counter-test -> admitted (refuted_finding)", "refuted_finding" in verdicts)
    afc = [o for o in ct["countertest_outcomes"]
           if o.get("rejection_code") == "REJECTED_AFFIRMING_THE_CONSEQUENT"]
    check("ctest: affirming-the-consequent -> confirmed + D1 rejection code",
          len(afc) == 1 and afc[0]["verdict"] == "confirmed_finding")
    check("ctest: output schema-conformant + sealed",
          not validate_artifact(ct) and verify_seal(ct, seal(ct)))
    # non-conformant runner output must be REJECTED
    bad = dict(ct); bad["countertest_outcomes"] = [{"outcome_id": "x"}]  # missing required fields
    check("ctest: non-conformant output REJECTED", bool(validate_artifact(bad)))

    # 6) determinism
    a = produce_bias_passport(ns, _example_detections(), run_id="st")
    b = produce_bias_passport(ns, _example_detections(), run_id="st")
    check("determinism: same input -> byte-identical output", canonical(a) == canonical(b))

    passed = sum(1 for _, ok in checks if ok)
    for label, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
    print(f"\n{passed}/{len(checks)} hygiene-runtime checks passed")
    return 0 if passed == len(checks) else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Epistemic-hygiene runtime")
    ap.add_argument("--selftest", action="store_true", help="run teeth self-test")
    ap.add_argument("--emit-examples", metavar="DIR", help="emit deterministic example artifacts")
    args = ap.parse_args(argv)
    ns = Namespace.load()
    if args.emit_examples:
        emit_examples(ns, Path(args.emit_examples))
        return 0
    # default action is the self-test (what CI runs)
    return selftest(ns)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
