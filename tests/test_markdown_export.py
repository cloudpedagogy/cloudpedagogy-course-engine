from pathlib import Path

from course_engine.schema import validate_course_dict
from course_engine.exporters.markdown import build_markdown_package


def test_markdown_export_creates_files(tmp_path: Path):
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
                            "learning_objectives": ["Do thing"],
                            "content_blocks": [{"type": "markdown", "body": "Hello"}],
                        }
                    ],
                }
            ]
        },
    }

    spec = validate_course_dict(data)
    out_dir = build_markdown_package(spec, out_root=tmp_path)

    assert (out_dir / "course.md").exists()
    assert (out_dir / "lessons").exists()

    lesson_files = list((out_dir / "lessons").glob("*.md"))
    assert len(lesson_files) == 1
    text = lesson_files[0].read_text(encoding="utf-8")
    assert "# Lesson 1" in text
    assert "## Learning objectives" in text
