# tests/test_pack_profiles.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from course_engine.pack.packer import run_pack
from course_engine.pack.profiles import resolve_pack_profile


def _write_minimal_artefact_dir(dist_dir: Path, *, with_capability_mapping: bool = False) -> None:
    """
    Create a minimal dist/<course-id> directory that looks like an artefact input to pack:
    - must contain manifest.json
    - include capability_mapping optionally to trigger report generation
    """
    dist_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "course": {"id": "t", "title": "Test", "version": "0.0.0"},
        "output": {"format": "quarto", "out_dir": str(dist_dir)},
        "builder": {"name": "course-engine", "version": "test", "python": "test"},
        "built_at_utc": "2026-01-01T00:00:00Z",
        "files": [],
    }

    if with_capability_mapping:
        # Minimal shape: packer checks truthiness and report builder expects fields to exist.
        # Keep it small but structurally plausible.
        manifest["capability_mapping"] = {
            "framework": "CloudPedagogy AI Capability Framework (2026 Edition)",
            "version": "test",
            "domains_declared": 1,
            "domains": {"Awareness": {"coverage": [], "evidence": []}},
            "status": "informational",
        }

    (dist_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _list_names(p: Path) -> set[str]:
    return {x.name for x in p.iterdir() if x.is_file()}


def test_resolve_pack_profile_known_profiles():
    # Sanity lock: these profile names are part of the v1.18 contract
    for name in ("audit", "qa", "minimal"):
        items = resolve_pack_profile(name)
        assert items, f"Expected non-empty profile items for {name}"


def test_pack_profile_minimal_includes_only_readme_and_summary(tmp_path: Path):
    dist_dir = tmp_path / "dist" / "course-x"
    _write_minimal_artefact_dir(dist_dir, with_capability_mapping=True)

    out_dir = tmp_path / "packs" / "minimal"
    result = run_pack(
        input_path=dist_dir,
        out_dir=out_dir,
        engine_version="test",
        command="pytest",
        profile="minimal",
    )

    names = _list_names(out_dir)

    # Always present
    assert "pack_manifest.json" in names

    # Profile contract
    assert "README.txt" in names
    assert "summary.txt" in names

    # Not in minimal
    assert "explain.json" not in names
    assert "explain.txt" not in names
    assert "manifest.json" not in names
    assert "report.json" not in names
    assert "report.txt" not in names

    # CLI-friendly contents flags should match physical outputs
    contents = (result or {}).get("contents") or {}
    assert contents.get("readme_txt") is True
    assert contents.get("summary_txt") is True
    assert contents.get("explain_txt") is False
    assert contents.get("explain_json") is False
    assert contents.get("manifest_json") is False
    assert contents.get("report_txt") is False
    assert contents.get("report_json") is False


def test_pack_profile_qa_includes_explain_and_manifest_and_report_if_present(tmp_path: Path):
    dist_dir = tmp_path / "dist" / "course-x"
    _write_minimal_artefact_dir(dist_dir, with_capability_mapping=True)

    out_dir = tmp_path / "packs" / "qa"
    result = run_pack(
        input_path=dist_dir,
        out_dir=out_dir,
        engine_version="test",
        command="pytest",
        profile="qa",
    )

    names = _list_names(out_dir)

    # Always present
    assert "pack_manifest.json" in names

    # QA profile contract
    assert "README.txt" in names
    assert "summary.txt" in names
    assert "explain.json" in names
    assert "explain.txt" in names
    assert "manifest.json" in names

    # Because we included capability_mapping
    assert "report.json" in names
    assert "report.txt" in names

    contents = (result or {}).get("contents") or {}
    assert contents.get("readme_txt") is True
    assert contents.get("summary_txt") is True
    assert contents.get("explain_txt") is True
    assert contents.get("explain_json") is True
    assert contents.get("manifest_json") is True
    assert contents.get("report_txt") is True
    assert contents.get("report_json") is True


def test_pack_profile_qa_omits_report_when_capability_mapping_absent(tmp_path: Path):
    dist_dir = tmp_path / "dist" / "course-x"
    _write_minimal_artefact_dir(dist_dir, with_capability_mapping=False)

    out_dir = tmp_path / "packs" / "qa"
    result = run_pack(
        input_path=dist_dir,
        out_dir=out_dir,
        engine_version="test",
        command="pytest",
        profile="qa",
    )

    names = _list_names(out_dir)

    assert "pack_manifest.json" in names
    assert "README.txt" in names
    assert "summary.txt" in names
    assert "explain.json" in names
    assert "explain.txt" in names
    assert "manifest.json" in names

    # No capability mapping => no report outputs
    assert "report.json" not in names
    assert "report.txt" not in names

    contents = (result or {}).get("contents") or {}
    assert contents.get("report_txt") is False
    assert contents.get("report_json") is False


def test_pack_unknown_profile_raises_value_error(tmp_path: Path):
    dist_dir = tmp_path / "dist" / "course-x"
    _write_minimal_artefact_dir(dist_dir, with_capability_mapping=False)

    out_dir = tmp_path / "packs" / "bad"

    with pytest.raises(ValueError):
        run_pack(
            input_path=dist_dir,
            out_dir=out_dir,
            engine_version="test",
            command="pytest",
            profile="nonsense",
        )
