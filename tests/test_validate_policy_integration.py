# tests/test_validate_policy_integration.py

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()


def _write_manifest(build_dir: Path, *, domains: dict, signals: list | None = None) -> None:
    """
    Write a minimal manifest.json that load_manifest() and build_capability_report()
    can consume.

    domains format:
      {
        "awareness": {"label": "...", "intent": "...", "coverage": [...], "evidence": [...]},
        ...
      }

    v1.13+: manifest_version bumped to 1.4.0 and may include `signals`.
    """
    manifest = {
        "manifest_version": "1.4.0",
        "built_at_utc": "2026-01-09T00:00:00Z",
        "builder": {"name": "course-engine", "version": "1.13.0", "python": "3.x"},
        "input": {"course_yml": "example/course.yml"},
        "course": {"id": "test-course", "title": "Test Course", "version": "0.1.0"},
        "output": {"format": "quarto", "out_dir": str(build_dir)},
        "files": [],
        # v1.13+: signals list
        "signals": signals or [],
        "capability_mapping": {
            "framework": "Example Framework",
            "version": "1",
            "status": "informational",
            "domains_declared": len(domains),
            "domains": domains,
        },
    }
    (build_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_policy(path: Path) -> None:
    """
    Write a strict policy that requires >=4 declared domains and >=1 evidence item per domain.
    This should fail against a manifest that declares only 3 domains.
    """
    policy_text = """\
policy_version: 1
policy_id: "test-policy"
policy_name: "Test Policy"
default_profile: "strict"

profiles:
  strict:
    description: "Strict thresholds for integration tests"
    rules:
      require_coverage:
        min_domains: 4
      require_evidence:
        min_items_per_domain: 1
      min_coverage_items_per_domain: 1
      forbid_empty_domains: true
"""
    path.write_text(policy_text, encoding="utf-8")


def _write_policy_with_signal_escalation(path: Path) -> None:
    """
    v1.13+: policy that escalates a specific signal to error.
    """
    policy_text = """\
policy_version: 1
policy_id: "test-policy-signals"
policy_name: "Test Policy (Signals)"
default_profile: "strict"

profiles:
  strict:
    description: "Signal escalation for integration tests"
    rules:
      require_coverage:
        min_domains: 1
    signals:
      default_action: info
      overrides:
        SIG-INTENT-001: error
"""
    path.write_text(policy_text, encoding="utf-8")


def test_policy_thresholds_change_validation_output(tmp_path: Path):
    """
    Expected behaviour:
      - validation without --policy uses engine default thresholds
      - validation with --policy + --profile applies policy thresholds, producing different output
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # 3 domains declared (should FAIL policy min_domains:4)
    domains = {
        "awareness": {
            "label": "AI Awareness",
            "intent": "Basics",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
        "decision_governance": {
            "label": "Governance",
            "intent": "Decisions",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
        "reflection_renewal": {
            "label": "Reflection",
            "intent": "Improve",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
    }
    _write_manifest(build_dir, domains=domains)

    policy_path = tmp_path / "policy.yml"
    _write_policy(policy_path)

    # Baseline run (no policy): should NOT reflect the stricter policy threshold.
    r0 = runner.invoke(app, ["validate", str(build_dir)])
    assert r0.exit_code in (0, 3), r0.output  # depends on strict default behaviour
    assert "minimum required is 4" not in r0.output.lower()

    # Policy run: should mention min_domains=4 violation in output (as a warning in non-strict mode).
    r1 = runner.invoke(
        app,
        [
            "validate",
            str(build_dir),
            "--policy",
            str(policy_path),
            "--profile",
            "strict",
        ],
    )
    assert r1.exit_code == 0, r1.output  # non-strict default should not fail the process

    out1 = r1.output.lower()
    assert "require_coverage" in out1, r1.output
    assert "only 3 domains declared" in out1, r1.output
    assert "minimum required is 4" in out1, r1.output


def test_policy_strict_mode_sets_nonzero_exit_on_violations(tmp_path: Path):
    """
    Expected behaviour:
      - with --strict enabled, policy violations should produce a non-zero exit code
      - threshold should still be taken from policy (min_domains: 4)
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # 3 domains declared (policy requires 4)
    domains = {
        "awareness": {
            "label": "AI Awareness",
            "intent": "Basics",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
        "decision_governance": {
            "label": "Governance",
            "intent": "Decisions",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
        "reflection_renewal": {
            "label": "Reflection",
            "intent": "Improve",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
    }
    _write_manifest(build_dir, domains=domains)

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
            "strict",
            "--strict",
        ],
    )

    # Exit code 3 is your current strict-fail convention in cli.validate
    assert r.exit_code == 3, r.output

    out = r.output.lower()
    assert "require_coverage" in out, r.output
    assert "only 3 domains declared" in out, r.output
    assert "minimum required is 4" in out, r.output


def test_signal_escalation_to_error_can_fail_validation_even_without_strict(tmp_path: Path):
    """
    v1.13+: If policy interprets a signal as action=error, validation should fail
    even without --strict (CI gating behaviour).

    This locks in the CLI rule:
      - non-strict exits non-zero ONLY when signal action resolves to "error"
        (rules violations remain warnings unless --strict is set).
    """
    from course_engine.cli import app

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    domains = {
        "awareness": {
            "label": "AI Awareness",
            "intent": "Basics",
            "coverage": ["m1"],
            "evidence": ["lesson:l1"],
        },
    }

    # Inject one signal that the policy will escalate to error
    signals = [
        {
            "id": "SIG-INTENT-001",
            "severity": "info",
            "summary": "Design intent not declared",
            "detail": "course.yml has no design_intent block.",
            "evidence": [],
            "review_question": "Should this course declare design intent for governance review?",
            "source": "manifest",
            "tags": ["governance"],
        }
    ]

    _write_manifest(build_dir, domains=domains, signals=signals)

    policy_path = tmp_path / "policy-signals.yml"
    _write_policy_with_signal_escalation(policy_path)

    r = runner.invoke(
        app,
        [
            "validate",
            str(build_dir),
            "--policy",
            str(policy_path),
            "--profile",
            "strict",
        ],
    )

    # CI gating rule: signal action=error should exit 3 even without --strict
    assert r.exit_code == 3, r.output

    out = r.output.lower()
    # The issue is emitted as a validation issue with rule="signal:SIG-INTENT-001"
    assert "signal:sig-intent-001" in out, r.output
