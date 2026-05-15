import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "import_superconscious_reasoning.py"
FIXTURE = ROOT / "examples" / "superconscious" / "deterministic"


def load_importer():
    spec = importlib.util.spec_from_file_location("import_superconscious_reasoning", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_superconscious_reasoning_fixture_imports_cleanly():
    importer = load_importer()

    report = importer.validate_superconscious_run(FIXTURE)

    assert report["result"] == "pass"
    assert report["summary"]["runId"] == "urn:srcos:reasoning-run:agentplane-fixture"
    assert report["summary"]["replayClass"] == "exact"
    assert report["summary"]["benchmarkPassed"] is True
    assert report["summary"]["rawPrivateReasoning"] == "not-collected"
    assert report["errors"] == []


def test_superconscious_reasoning_fixture_fails_when_benchmark_missing(tmp_path):
    importer = load_importer()
    for source in FIXTURE.iterdir():
        target = tmp_path / source.name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "reasoning-benchmark.json").unlink()

    report = importer.validate_superconscious_run(tmp_path)

    assert report["result"] == "fail"
    assert "missing canonical artifact: reasoning-benchmark.json" in report["errors"]
