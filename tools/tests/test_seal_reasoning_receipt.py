from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "seal_reasoning_receipt.py"

EVIDENCE_ID_PREFIX = "urn:srcos:evidence:sealed-reasoning:"
RUN_HEX = "fa087eaaa55140e083b6aff70bd1cd0b"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _valid_receipt() -> dict:
    return {
        "id": "urn:srcos:receipt:reasoning:580d341e15e34a5192598b8023fc9373",
        "type": "ReasoningReceipt",
        "specVersion": "2.0.0",
        "runRef": f"urn:srcos:reasoning-run:{RUN_HEX}",
        "taskRef": f"urn:srcos:reasoning-task:{RUN_HEX}",
        "status": "completed",
        "traceHash": "sha256:981871aa8520b8c1f774731532f885d576a9521852372886021627d633e59c0d",
        "replayClass": "non-replayable-side-effect",
        "capturedAt": "2026-06-22T02:47:24.628464Z",
    }


def _valid_run() -> dict:
    return {
        "id": f"urn:srcos:reasoning-run:{RUN_HEX}",
        "type": "ReasoningRun",
        "specVersion": "2.0.0",
        "status": "completed",
        "traceHash": "sha256:981871aa8520b8c1f774731532f885d576a9521852372886021627d633e59c0d",
    }


def _write_fixture(tmp: Path) -> tuple[Path, Path, Path]:
    receipt_path = tmp / "receipt.json"
    run_path = tmp / "run.json"
    events_path = tmp / "reasoning-events.ndjson"
    receipt_path.write_text(json.dumps(_valid_receipt()), encoding="utf-8")
    run_path.write_text(json.dumps(_valid_run()), encoding="utf-8")
    events_path.write_text(
        '{"id": "urn:srcos:reasoning-event:aaa", "type": "ReasoningEvent"}\n'
        '{"id": "urn:srcos:reasoning-event:bbb", "type": "ReasoningEvent"}\n',
        encoding="utf-8",
    )
    return receipt_path, run_path, events_path


def test_seal_verify_roundtrip_and_tamper() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        receipt_path, run_path, events_path = _write_fixture(tmp)
        out_dir = tmp / "out"

        # 1 + 2. Seal.
        result = _run(
            [
                "--receipt",
                str(receipt_path),
                "--run",
                str(run_path),
                "--events",
                str(events_path),
                "--out-dir",
                str(out_dir),
            ]
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["sealed"] is True
        assert payload["evidence_id"].startswith(EVIDENCE_ID_PREFIX)
        sealed_path = Path(payload["sealed_path"])
        assert sealed_path.exists()
        assert sealed_path.name.endswith(".sealed.json")
        # Ledger pointer written.
        assert (out_dir / "sealed-index.ndjson").exists()

        # 3. Verify -> true.
        verify = _run(["--verify", str(sealed_path)])
        assert verify.returncode == 0, verify.stderr
        vpayload = json.loads(verify.stdout)
        assert vpayload["verified"] is True
        assert vpayload["evidence_id"] == payload["evidence_id"]

        # 4. Tamper test: mutate a field inside the embedded receipt.
        record = json.loads(sealed_path.read_text(encoding="utf-8"))
        record["receipt"]["status"] = "failed"
        tampered_path = out_dir / "tampered.sealed.json"
        tampered_path.write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        tampered = _run(["--verify", str(tampered_path)])
        assert tampered.returncode != 0
        tpayload = json.loads(tampered.stdout)
        assert tpayload["verified"] is False
        assert "reason" in tpayload


def test_seal_receipt_only_no_companions() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        receipt_path = tmp / "receipt.json"
        receipt_path.write_text(json.dumps(_valid_receipt()), encoding="utf-8")
        out_dir = tmp / "out"
        result = _run(["--receipt", str(receipt_path), "--out-dir", str(out_dir)])
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["sealed"] is True
        verify = _run(["--verify", payload["sealed_path"]])
        assert verify.returncode == 0, verify.stderr
        assert json.loads(verify.stdout)["verified"] is True


def test_invalid_receipt_missing_required_field_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        receipt = _valid_receipt()
        del receipt["traceHash"]
        receipt_path = tmp / "receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        out_dir = tmp / "out"
        result = _run(["--receipt", str(receipt_path), "--out-dir", str(out_dir)])
        assert result.returncode != 0
        payload = json.loads(result.stdout)
        assert payload["sealed"] is False
        assert "receipt failed validation" in payload["reason"]
        assert "traceHash" in payload["reason"]


if __name__ == "__main__":
    test_seal_verify_roundtrip_and_tamper()
    test_seal_receipt_only_no_companions()
    test_invalid_receipt_missing_required_field_fails()
    print("OK: all seal_reasoning_receipt tests passed")
