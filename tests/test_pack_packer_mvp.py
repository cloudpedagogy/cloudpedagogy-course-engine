# tests/test_pack_packer_mvp.py

from __future__ import annotations

import json
from pathlib import Path

from course_engine.pack.packer import run_pack


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
        engine_version="1.16.0-test",
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
    assert pm["pack"]["engine"]["version"] == "1.16.0-test"
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
