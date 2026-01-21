from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()

TOP_LEVEL_KEYS_V18_EXPLAIN = [
    "explain_schema_version",
    "engine",
    "input",
    "course",
    "structure",
    "sources",
    "policies",
    "rendering",
    "capability_mapping",
    # v1.13: absence signals surfaced in course.yml explain
    "signals",
    "warnings",
    "errors",
]


def _write_policy(path: Path) -> None:
    """
    Write a minimal policy with one profile so we can exercise:
      validate <dir> --policy <file> --profile <name> --explain --json
    """
    policy_text = """\
policy_version: 1
policy_id: "test-policy"
policy_name: "Test Policy"
owner: "Test Owner"
default_profile: "baseline"

profiles:
  baseline:
    description: "Baseline thresholds"
    rules:
      require_coverage:
        min_domains: 1
      require_evidence:
        min_items_per_domain: 0
      min_coverage_items_per_domain: 0
      forbid_empty_domains: false
"""
    path.write_text(policy_text, encoding="utf-8")


# ---------------------------------------------------------------------
# v1.5: validate --explain --json (policy/profile explain-only)
# ---------------------------------------------------------------------


def test_explain_json_with_preset_does_not_require_manifest(tmp_path: Path):
    """
    v1.5 requirement:
      - --explain --json is explain-only
      - It must succeed even if manifest.json is missing
      - Output must be valid JSON
      - Output must include core explain fields (policy/profile/chain/rules/strict)
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    r = runner.invoke(
        app,
        [
            "validate",
            str(build_dir),
            "--policy",
            "preset:baseline",
            "--profile",
            "baseline",
            "--explain",
            "--json",
        ],
    )
    assert r.exit_code == 0, r.output

    data = json.loads(r.output)

    # Minimal required structure for governance/debug pipelines
    assert "policy" in data
    assert "profile" in data
    assert "rules" in data
    assert "chain" in data
    assert "strict" in data

    assert data["policy"]["source"].startswith("preset:"), data
    assert data["profile"]["name"] == "baseline", data
    assert isinstance(data["chain"], list), data
    assert isinstance(data["rules"], dict), data
    assert isinstance(data["strict"], bool), data


def test_explain_json_with_file_policy_includes_provenance(tmp_path: Path):
    """
    v1.5 requirement:
      - provenance metadata is surfaced (informational only)
      - still explain-only, still JSON
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    policy_path = tmp_path / "policy.yml"
    _write_policy(policy_path)

    r = runner.invoke(
        app,
        [
            "validate",
            str(build_dir),
            "--policy",
            str(policy_path),
            "--profile",
            "baseline",
            "--explain",
            "--json",
        ],
    )
    assert r.exit_code == 0, r.output

    data = json.loads(r.output)

    assert data["policy"]["source"] == str(policy_path), data
    # provenance (optional, but expected to appear when provided)
    assert data["policy"].get("policy_id") == "test-policy", data
    assert data["policy"].get("policy_name") == "Test Policy", data
    assert data["policy"].get("owner") == "Test Owner", data


def test_explain_json_respects_strict_flag(tmp_path: Path):
    """
    v1.5 requirement:
      - strict status is reported in explain JSON
      - explain still does not execute validation
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    r = runner.invoke(
        app,
        [
            "validate",
            str(build_dir),
            "--policy",
            "preset:baseline",
            "--profile",
            "baseline",
            "--explain",
            "--json",
            "--strict",
        ],
    )
    assert r.exit_code == 0, r.output

    data = json.loads(r.output)
    assert data["strict"] is True, data


# ---------------------------------------------------------------------
# v1.8: course-engine explain <course.yml> --json (course.yml explainability)
# ---------------------------------------------------------------------


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sample_course_yml() -> Path:
    """
    Prefer the canonical example path in this repo.
    Adjust here if you relocate the sample.
    """
    p = _repo_root() / "examples" / "sample-course" / "course.yml"
    if not p.exists():
        # fallback to demo sample if examples not present in some contexts
        alt = _repo_root() / "demo" / "scenario-planning-environmental-scanning" / "course.yml"
        if alt.exists():
            return alt
    return p


def test_course_explain_json_schema_keys():
    """
    v1.8 requirement:
      - `course-engine explain <course.yml> --json` outputs valid JSON
      - includes required top-level keys
      - includes rendering defaults (toc/toc_depth)

    v1.13 extension:
      - includes top-level `signals` (may be empty, but must be present)
    """
    from course_engine.cli import app

    course_yml = _sample_course_yml()
    assert course_yml.exists(), f"Expected sample course.yml to exist at: {course_yml}"

    r = runner.invoke(app, ["explain", str(course_yml), "--json"])
    assert r.exit_code == 0, r.output

    payload = json.loads(r.output)

    assert payload.get("explain_schema_version") == "1.0", payload

    for k in TOP_LEVEL_KEYS_V18_EXPLAIN:
        assert k in payload, f"Missing top-level key: {k}"

    # engine provenance
    assert payload["engine"]["name"] == "cloudpedagogy-course-engine"
    assert isinstance(payload["engine"].get("version"), str)
    assert isinstance(payload["engine"].get("built_at_utc"), str)

    # input details
    assert payload["input"]["type"] == "course_yml"
    assert payload["input"]["exists"] is True
    assert isinstance(payload["input"]["hash_sha256"], str)
    assert isinstance(payload["input"]["bytes"], int)

    # rendering defaults
    assert payload["rendering"]["quarto"]["toc"] is True
    assert payload["rendering"]["quarto"]["toc_depth"] == 2

    # v1.13: signals surface (may be empty, but must be present + list)
    assert isinstance(payload["signals"], list)

    # warnings/errors arrays
    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["errors"], list)


def test_course_explain_signals_shape_and_order():
    """
    v1.13 requirement (AC-SIGNAL-003 / AC-SIGNAL-004):
      - `signals` exists and is a list
      - each signal contains required keys
      - signal ordering is deterministic (sorted by id)

    Note: we avoid asserting exact signal *content* here (examples may evolve),
    only the contract shape and ordering.
    """
    from course_engine.cli import app

    course_yml = _sample_course_yml()
    assert course_yml.exists(), f"Expected sample course.yml to exist at: {course_yml}"

    r = runner.invoke(app, ["explain", str(course_yml), "--json"])
    assert r.exit_code == 0, r.output

    payload = json.loads(r.output)
    signals = payload.get("signals")
    assert isinstance(signals, list), payload

    # Required schema keys per-signal
    required = {"id", "severity", "summary", "detail", "evidence"}

    for s in signals:
        assert isinstance(s, dict), s
        missing = required.difference(s.keys())
        assert not missing, f"Signal missing required keys: {missing} in {s}"
        assert s["severity"] in ("info", "warning"), s
        assert isinstance(s["evidence"], list), s

    # Deterministic ordering: ids are sorted
    ids = [s.get("id") for s in signals]
    # If there are signals, ensure they're all strings and ordered.
    for _id in ids:
        assert isinstance(_id, str), ids
    assert ids == sorted(ids), ids


def test_course_explain_json_only_runtime_metadata_varies():
    """
    v1.8 determinism policy:
      - output is deterministic given identical inputs
      - exception: engine.built_at_utc may vary

    v1.13:
      - signals are included in deterministic comparison (must not vary)
    """
    from course_engine.cli import app

    course_yml = _sample_course_yml()
    assert course_yml.exists(), f"Expected sample course.yml to exist at: {course_yml}"

    r1 = runner.invoke(app, ["explain", str(course_yml), "--json"])
    assert r1.exit_code == 0, r1.output
    p1 = json.loads(r1.output)

    r2 = runner.invoke(app, ["explain", str(course_yml), "--json"])
    assert r2.exit_code == 0, r2.output
    p2 = json.loads(r2.output)

    # redact allowed non-deterministic field
    p1["engine"]["built_at_utc"] = "<redacted>"
    p2["engine"]["built_at_utc"] = "<redacted>"

    assert p1 == p2
