from __future__ import annotations

import json
from pathlib import Path

from course_engine.explain.artefact import explain_dist_dir


def test_explain_dist_surfaces_manifest_signals(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": "1.4.0",
        "built_at_utc": "2026-01-21T00:00:00Z",
        "builder": {"name": "course-engine", "version": "test", "python": "3.x", "platform": "test"},
        "input": {"course_yml": "course.yml"},
        "course": {"id": "c1", "title": "Course", "version": "0.1.0"},
        "output": {"format": "html", "out_dir": str(dist_dir)},
        "files": [{"path": "index.qmd", "bytes": 1, "sha256": "x"}],
        "signals": [
            {
                "id": "SIG-INTENT-001",
                "severity": "info",
                "summary": "Design intent not declared",
                "detail": "…",
                "evidence": ["course.yml:design_intent"],
            }
        ],
    }

    (dist_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    out = explain_dist_dir(dist_dir, engine_version="test", command="explain dist")
    assert "signals" in out
    assert isinstance(out["signals"], list)
    assert out["signals"][0]["id"] == "SIG-INTENT-001"
