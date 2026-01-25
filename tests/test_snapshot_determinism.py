"""
Determinism test for the v1.21+ governance snapshot contract.

Goal:
- Running `course-engine snapshot` twice on the same input should produce
  identical JSON output after removing timestamp-like fields.

Notes:
- This is intentionally strict to protect CI/governance diffability.
- If additional non-deterministic fields are introduced in the future,
  they should be explicitly normalised here (by design, not by accident).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    # tests/ is at repo_root/tests/
    return Path(__file__).resolve().parents[1]


def _pick_course_yml(root: Path) -> Path:
    candidates = [
        root / "examples" / "sample-course" / "course.yml",
        root / "demo" / "tmp.course.yml" / "course.yml",
        root / "demo" / "scenario-planning-environmental-scanning" / "course.yml",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Could not find a sample course.yml. Tried:\n"
        + "\n".join(str(p) for p in candidates)
    )


def _run_snapshot_json(course_yml: Path) -> dict:
    """
    Runs the CLI via `python -m course_engine ...` to avoid requiring an installed console script.
    Assumes v1.21+ provides: course-engine snapshot PATH --format json
    """
    cmd = [
        sys.executable,
        "-m",
        "course_engine",
        "snapshot",
        str(course_yml),
        "--format",
        "json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        # Print stderr/stdout to make CI failures actionable.
        raise AssertionError(
            "snapshot command failed.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"returncode: {res.returncode}\n"
            f"stdout:\n{res.stdout}\n"
            f"stderr:\n{res.stderr}\n"
        )

    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(
            "snapshot did not return valid JSON.\n"
            f"stdout:\n{res.stdout}\n"
            f"stderr:\n{res.stderr}\n"
            f"error: {e}\n"
        )


def _normalise_snapshot(s: dict) -> dict:
    """
    Remove or normalise fields that are expected to vary run-to-run.
    We keep this list intentionally small.
    """
    s = dict(s)  # shallow copy
    s.pop("generated_at_utc", None)
    return s


@pytest.mark.smoke
def test_snapshot_json_is_deterministic():
    root = _repo_root()
    course_yml = _pick_course_yml(root)

    snap1 = _normalise_snapshot(_run_snapshot_json(course_yml))
    snap2 = _normalise_snapshot(_run_snapshot_json(course_yml))

    assert snap1 == snap2, (
        "Snapshot JSON output is not deterministic (timestamps aside).\n"
        "If you added new fields, ensure they are stable or explicitly normalised.\n"
    )
