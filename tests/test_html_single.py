from pathlib import Path

from course_engine.generator.html_single import build_html_single_project
from course_engine.schema import validate_course_dict


def test_build_html_single_project_creates_files(tmp_path: Path):
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
        "structure": {
            "modules": [
                {"id": "m1", "title": "Module 1", "lessons": [{"id": "l1", "title": "Lesson 1"}]},
            ]
        },
    }
    spec = validate_course_dict(data)
    templates_dir = Path(__file__).resolve().parents[1] / "templates"

    out_dir = build_html_single_project(spec, out_root=tmp_path, templates_dir=templates_dir)

    assert (out_dir / "_quarto.yml").exists()
    assert (out_dir / "index.qmd").exists()
    assert "Lesson 1" in (out_dir / "index.qmd").read_text(encoding="utf-8")
