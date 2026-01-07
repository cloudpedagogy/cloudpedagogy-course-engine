from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from course_engine.schema import validate_course_dict
from course_engine.generator.build import build_quarto_project


pytestmark = pytest.mark.skipif(
    shutil.which("quarto") is None,
    reason="Quarto not installed (CI environment). Install Quarto or run tests locally with Quarto available.",
)


def test_build_creates_expected_files(tmp_path: Path):
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
        "structure": {
            "modules": [
                {
                    "id": "m1",
                    "title": "Module 1",
                    "lessons": [
                        {
                            "id": "l1",
                            "title": "Lesson 1",
                            "content_blocks": [{"type": "markdown", "body": "Hello"}],
                        }
                    ],
                }
            ]
        },
    }

    spec = validate_course_dict(data)
    repo_templates = Path(__file__).resolve().parents[1] / "templates"

    out_dir = build_quarto_project(spec, out_root=tmp_path, templates_dir=repo_templates)

    # Assert that core project files exist
    assert (out_dir / "_quarto.yml").exists()
    assert (out_dir / "index.qmd").exists()

    # Lessons index + one lesson page
    assert (out_dir / "lessons" / "index.qmd").exists()
    lesson_files = list((out_dir / "lessons").glob("m1-l1-*.qmd"))
    assert len(lesson_files) == 1
