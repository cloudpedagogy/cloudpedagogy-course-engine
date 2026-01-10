from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()


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
