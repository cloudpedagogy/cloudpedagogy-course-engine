from __future__ import annotations

from pathlib import Path

from course_engine.schema import validate_course_dict
from course_engine.utils.manifest import build_manifest


def test_capability_mapping_parses_into_spec():
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "capability_mapping": {
            "framework": "Framework",
            "version": "2026",
            "domains": {
                "awareness": {
                    "label": "AI Awareness & Orientation",
                    "intent": "Introduce foundations",
                    "coverage": ["m1"],
                    "evidence": ["lesson:l1"],
                }
            },
        },
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

    assert spec.capability_mapping is not None
    assert spec.capability_mapping.framework == "Framework"
    assert spec.capability_mapping.version == "2026"
    assert "awareness" in spec.capability_mapping.domains
    d = spec.capability_mapping.domains["awareness"]
    assert d.label == "AI Awareness & Orientation"
    assert d.intent == "Introduce foundations"
    assert d.coverage == ["m1"]
    assert d.evidence == ["lesson:l1"]


def test_manifest_includes_capability_mapping(tmp_path: Path):
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "capability_mapping": {
            "framework": "Framework",
            "version": "2026",
            "domains": {
                "awareness": {
                    "label": "AI Awareness & Orientation",
                    "intent": "Introduce foundations",
                    "coverage": ["m1"],
                    "evidence": ["lesson:l1"],
                }
            },
        },
        "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
        "structure": {"modules": []},
    }

    spec = validate_course_dict(data)

    # create a tiny fake output dir with one file so inventory isn't empty
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.qmd").write_text("# Test\n", encoding="utf-8")

    manifest = build_manifest(
        spec=spec,
        out_dir=out_dir,
        output_format="quarto",
        source_course_yml=None,
        include_hashes=False,
        include_sizes=False,
    )

    assert "capability_mapping" in manifest
    cap = manifest["capability_mapping"]
    assert cap["framework"] == "Framework"
    assert cap["version"] == "2026"
    assert cap["domains_declared"] == 1
    assert "awareness" in cap["domains"]
    assert cap["domains"]["awareness"]["label"] == "AI Awareness & Orientation"
