# tests/test_pack_packer_mvp.py

from __future__ import annotations

import json
from pathlib import Path

import pytest

from course_engine.pack.packer import PackInputError, run_pack


def test_pack_packer_mvp_on_dist_artefact(tmp_path: Path) -> None:
    """
    MVP test for governance pack generation from a dist artefact.

    This test asserts:
    - core pack files are written
    - pack_manifest.json follows the approved contract
    - returned runtime flags align with written artefacts
    """

    # Use an existing dist artefact in the repo
    artefact_dir = Path("dist/scenario-planning-environmental-scanning")
    assert artefact_dir.exists(), "Expected demo dist artefact to exist for this test."

    out_dir = tmp_path / "pack-out"

    result = run_pack(
        input_path=artefact_dir,
        out_dir=out_dir,
        engine_version="1.17.0-test",
        command="course-engine pack dist/... --out ...",
    )

    # Core outputs must always exist
    assert (out_dir / "pack_manifest.json").exists()
    assert (out_dir / "explain.json").exists()
    assert (out_dir / "explain.txt").exists()
    assert (out_dir / "summary.txt").exists()

    # Artefact input must copy manifest.json
    assert (out_dir / "manifest.json").exists()

    # Files should not be empty
    assert (out_dir / "explain.json").stat().st_size > 0
    assert (out_dir / "pack_manifest.json").stat().st_size > 0

    # Load and validate pack manifest contract
    pm = json.loads((out_dir / "pack_manifest.json").read_text(encoding="utf-8"))

    assert pm["pack"]["engine"]["name"] == "course-engine"
    assert pm["pack"]["engine"]["version"] == "1.17.0-test"
    assert pm["pack"]["input"]["type"] == "artefact"

    contents = pm["contents"]
    assert contents["explain_json"] is True
    assert contents["explain_txt"] is True
    assert contents["summary_txt"] is True
    assert contents["manifest_json"] is True

    # Returned runtime structure should align with manifest
    assert "contents" in result
    assert result["contents"]["explain_json"] is True
    assert result["contents"]["manifest_json"] is True


def test_pack_packer_accepts_parent_out_dir_with_single_artefact(tmp_path: Path) -> None:
    """
    v1.17: pack should accept a parent OUT directory if it contains exactly one
    child directory with manifest.json (auto-detect artefact dir).
    """
    parent_out = tmp_path / "out"
    artefact = parent_out / "course-123"
    artefact.mkdir(parents=True)
    (artefact / "manifest.json").write_text("{}", encoding="utf-8")

    out_dir = tmp_path / "pack-out"

    result = run_pack(
        input_path=parent_out,
        out_dir=out_dir,
        engine_version="1.17.0-test",
        command="course-engine pack OUTDIR --out ...",
    )

    # Must still produce core pack outputs
    assert (out_dir / "pack_manifest.json").exists()
    assert (out_dir / "explain.json").exists()
    assert (out_dir / "explain.txt").exists()
    assert (out_dir / "summary.txt").exists()

    # Should have copied manifest.json from the auto-detected artefact dir
    assert (out_dir / "manifest.json").exists()

    pm = json.loads((out_dir / "pack_manifest.json").read_text(encoding="utf-8"))
    assert pm["pack"]["input"]["type"] == "artefact"

    # Optional but valuable: confirm that resolution was recorded (notes)
    notes = pm.get("notes") or []
    assert any("resolved_input:" in str(n) for n in notes)

    # Returned runtime structure present
    assert "contents" in result
    assert result["contents"]["manifest_json"] is True


def test_pack_packer_parent_out_dir_with_no_candidates_errors(tmp_path: Path) -> None:
    """
    v1.17: if a parent OUT dir contains no artefact candidates, pack should
    fail with a clear, helpful error.
    """
    parent_out = tmp_path / "out"
    parent_out.mkdir(parents=True)

    out_dir = tmp_path / "pack-out"

    with pytest.raises(PackInputError) as e:
        run_pack(
            input_path=parent_out,
            out_dir=out_dir,
            engine_version="1.17.0-test",
            command="course-engine pack OUTDIR --out ...",
        )

    msg = str(e.value)
    assert "not recognised" in msg.lower()
    assert "manifest.json" in msg


def test_pack_packer_parent_out_dir_with_multiple_candidates_errors(tmp_path: Path) -> None:
    """
    v1.17: if a parent OUT dir contains multiple candidate artefact dirs,
    pack should fail with a helpful error listing candidates.
    """
    parent_out = tmp_path / "out"
    a1 = parent_out / "a"
    a2 = parent_out / "b"
    a1.mkdir(parents=True)
    a2.mkdir(parents=True)
    (a1 / "manifest.json").write_text("{}", encoding="utf-8")
    (a2 / "manifest.json").write_text("{}", encoding="utf-8")

    out_dir = tmp_path / "pack-out"

    with pytest.raises(PackInputError) as e:
        run_pack(
            input_path=parent_out,
            out_dir=out_dir,
            engine_version="1.17.0-test",
            command="course-engine pack OUTDIR --out ...",
        )

    msg = str(e.value)
    assert "multiple artefact candidates" in msg.lower()
    assert str(a1) in msg
    assert str(a2) in msg
