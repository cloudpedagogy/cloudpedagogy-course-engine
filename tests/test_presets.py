from __future__ import annotations

import pytest


def test_list_presets_includes_expected_names():
    from course_engine.utils.policy import list_presets

    names = list_presets()
    assert "baseline" in names
    assert "higher-ed-example" in names
    assert "strict-ci" in names


def test_load_preset_baseline():
    from course_engine.utils.policy import load_policy_source

    policy = load_policy_source("preset:baseline")
    assert policy["policy_version"] == 1
    assert "profiles" in policy
    assert "baseline" in policy["profiles"]


def test_unknown_preset_errors_with_available_names():
    from course_engine.utils.policy import load_policy_source

    with pytest.raises(ValueError) as e:
        load_policy_source("preset:nope")

    msg = str(e.value).lower()
    assert "preset" in msg
    assert "baseline" in msg  # should list valid presets
