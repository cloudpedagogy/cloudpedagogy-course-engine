from __future__ import annotations

from pathlib import Path

import yaml

from course_engine.explain.artefact import explain_dist_dir
from course_engine.generator.build import build_quarto_project
from course_engine.schema import validate_course_dict
from course_engine.utils.manifest import write_manifest


def test_explain_dist_dir_manifest_backed(tmp_path: Path) -> None:
    """
    v1.9: explain() should support dist/<course> directories by reading manifest.json,
    producing stable explain JSON (deterministic except engine.built_at_utc).

    This test is self-contained and relies only on committed repo fixtures under examples/.
    """
    repo_root = Path(__file__).resolve().parents[1]
    templates_dir = repo_root / "templates"

    # Use committed fixture (available in CI)
    course_yml = repo_root / "examples" / "sample-course" / "course.yml"
    assert course_yml.exists(), "examples/sample-course/course.yml missing (repo fixture expected)"
    assert templates_dir.exists(), "templates/ missing (repo fixture expected)"

    data = yaml.safe_load(course_yml.read_text(encoding="utf-8"))
    spec = validate_course_dict(data, source_course_yml=course_yml)

    out_root = tmp_path / "dist"
    out_dir = build_quarto_project(spec, out_root=out_root, templates_dir=templates_dir)

    # Emit manifest.json (so explain_dist_dir has what it needs)
    write_manifest(
        spec=spec,
        out_dir=out_dir,
        output_format="quarto",
        source_course_yml=course_yml,
        include_hashes=True,
    )

    payload_1 = explain_dist_dir(out_dir, engine_version="TEST", command="pytest")
    assert payload_1["input"]["type"] == "dist_dir"
    assert payload_1["errors"] == []
    assert payload_1["course"]["id"] == spec.id
    assert payload_1["course"]["title"] == spec.title
    assert payload_1["sources"]["counts"]["files"] > 0
    assert payload_1["sources"]["counts"]["missing"] == 0

    # Determinism check (except engine.built_at_utc)
    payload_2 = explain_dist_dir(out_dir, engine_version="TEST", command="pytest")
    payload_1["engine"]["built_at_utc"] = "X"
    payload_2["engine"]["built_at_utc"] = "X"
    assert payload_1 == payload_2
