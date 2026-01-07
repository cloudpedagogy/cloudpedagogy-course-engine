import pytest
from course_engine.schema import validate_course_dict


def test_validate_minimal_course():
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
        "structure": {
            "modules": [
                {
                    "id": "m1",
                    "title": "Module 1",
                    "lessons": [{"id": "l1", "title": "Lesson 1"}],
                }
            ]
        },
    }
    spec = validate_course_dict(data)
    assert spec.id == "test-course"
    assert spec.modules[0].lessons[0].title == "Lesson 1"


def test_invalid_course_id_raises():
    data = {
        "course": {"id": "BAD ID", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "structure": {"modules": []},
    }
    with pytest.raises(ValueError):
        validate_course_dict(data)


def test_quiz_block_semantics():
    data = {
        "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
        "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
        "structure": {
            "modules": [
                {
                    "id": "m1",
                    "title": "Module 1",
                    "lessons": [
                        {
                            "id": "l1",
                            "title": "Lesson 1",
                            "content_blocks": [
                                {
                                    "type": "quiz",
                                    "prompt": "Pick one",
                                    "options": ["A", "B"],
                                    "answer": 0,
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    }
    spec = validate_course_dict(data)
    assert spec.modules[0].lessons[0].content_blocks[0].type == "quiz"
