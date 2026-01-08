from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from course_engine.cli import app


runner = CliRunner()


def _write_manifest(out_dir: Path, manifest: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def test_report_human_output_success(tmp_path: Path):
    out_dir = tmp_path / "out"
    manifest = {
        "course": {"id": "c1", "title": "Course 1", "version": "0.1.0"},
        "output": {"format": "quarto", "out_dir": str(out_dir)},
        "capability_mapping": {
            "framework": "Framework",
            "version": "2026",
            "status": "informational (not enforced)",
            "domains_declared": 2,
            "domains": {
                "awareness": {"label": "Awareness", "coverage": ["m1"], "evidence": ["lesson:l1"]},
                "reflection": {"label": "Reflection", "coverage": [], "evidence": []},
            },
        },
        "files": [],
    }
    _write_manifest(out_dir, manifest)

    res = runner.invoke(app, ["report", str(out_dir)])
    assert res.exit_code == 0
    assert "Capability Coverage Report (v1.2)" in res.stdout
    assert "Domains with gaps: 1" in res.stdout
    assert "awareness" in res.stdout
    assert "reflection" in res.stdout


def test_report_json_output(tmp_path: Path):
    out_dir = tmp_path / "out"
    manifest = {
        "course": {"id": "c1", "title": "Course 1", "version": "0.1.0"},
        "capability_mapping": {
            "framework": "Framework",
            "version": "2026",
            "domains": {
                "awareness": {"label": "Awareness", "coverage": ["m1"], "evidence": ["lesson:l1"]},
            },
        },
        "files": [],
    }
    _write_manifest(out_dir, manifest)

    res = runner.invoke(app, ["report", str(out_dir), "--json"])
    assert res.exit_code == 0

    parsed = json.loads(res.stdout)
    assert parsed["capability_mapping"]["framework"] == "Framework"
    assert parsed["summary"]["gaps"] == 0
    assert "awareness" in parsed["domains"]


def test_report_missing_capability_mapping_exits_1(tmp_path: Path):
    out_dir = tmp_path / "out"
    manifest = {"course": {"id": "c1", "title": "Course 1", "version": "0.1.0"}, "files": []}
    _write_manifest(out_dir, manifest)

    res = runner.invoke(app, ["report", str(out_dir)])
    assert res.exit_code == 1
    assert "No capability_mapping found" in res.stdout


def test_report_fail_on_gaps_exits_2(tmp_path: Path):
    out_dir = tmp_path / "out"
    manifest = {
        "course": {"id": "c1", "title": "Course 1", "version": "0.1.0"},
        "capability_mapping": {
            "framework": "Framework",
            "version": "2026",
            "domains": {
                "awareness": {"label": "Awareness", "coverage": [], "evidence": []},
            },
        },
        "files": [],
    }
    _write_manifest(out_dir, manifest)

    res = runner.invoke(app, ["report", str(out_dir), "--fail-on-gaps"])
    assert res.exit_code == 2
    assert "Domains with gaps: 1" in res.stdout
