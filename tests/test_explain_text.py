from course_engine.explain.text import explain_payload_to_text


def test_explain_text_source_mode_renders_identity():
    payload = {
        "engine": {"version": "1.10.0", "built_at_utc": "2026-01-01T00:00:00Z"},
        "input": {"type": "course_yml", "path_normalised": "demo/course.yml"},
        "course": {"id": "c1", "title": "Course 1", "version": "0.1.0", "language": "en-GB"},
        "sources": {"files": [], "counts": {"files": 0}},
        "capability_mapping": {"present": False},
        "warnings": [],
        "errors": [],
    }

    text = explain_payload_to_text(payload)

    assert "Mode: source (course.yml)" in text
    assert "Title: Course 1" in text
    assert "ID: c1" in text


def test_explain_text_artefact_mode_renders_artefact_summary():
    payload = {
        "engine": {"version": "1.10.0", "built_at_utc": "2026-01-01T00:00:00Z"},
        "input": {"type": "dist_dir", "path_normalised": "dist/c1"},
        "course": {"id": "c1", "title": "Course 1", "version": "0.1.0", "language": "en"},
        "sources": {"files": [{"declared_path": "index.qmd"}], "counts": {"files": 1}},
        "rendering": {
            "artefact": {
                "manifest_version": "1.2.0",
                "built_at_utc": "2026-01-01T00:00:00Z",
                "builder": {"name": "course-engine", "version": "1.9.1", "python": "3.x", "platform": "x"},
                "output": {"format": "quarto", "out_dir": "dist/c1"},
                "input": {"course_yml": "demo/c1/course.yml"},
            }
        },
        "capability_mapping": {"present": False},
        "warnings": [],
        "errors": [],
    }

    text = explain_payload_to_text(payload)

    assert "Mode: artefact (manifest-backed)" in text
    assert "3. Artefact Summary" in text
    assert "Output format: quarto" in text
    assert "File count: 1" in text
