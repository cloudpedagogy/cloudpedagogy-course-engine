# tests/test_profile_resolution.py

from __future__ import annotations

import pytest


def test_default_profile_uses_default_profile_when_present():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "default_profile": "qa-lite",
        "profiles": {
            "baseline": {
                "rules": {
                    "require_coverage": {"min_domains": 1},
                    "require_evidence": {"min_items_per_domain": 0},
                    "min_coverage_items_per_domain": 0,
                    "forbid_empty_domains": False,
                }
            },
            "qa-lite": {
                "extends": "baseline",
                "rules": {
                    "require_coverage": {"min_domains": 4},
                    "require_evidence": {"min_items_per_domain": 1},
                },
            },
        },
    }

    resolved = resolve_profile(policy, profile=None)
    assert resolved["profile"] == "qa-lite"
    assert resolved["rules"]["require_coverage"]["min_domains"] == 4
    assert resolved["chain"] == ["baseline", "qa-lite"]


def test_default_profile_falls_back_to_baseline():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "profiles": {
            "baseline": {
                "rules": {
                    "require_coverage": {"min_domains": 1},
                    "require_evidence": {"min_items_per_domain": 0},
                    "min_coverage_items_per_domain": 0,
                    "forbid_empty_domains": False,
                }
            }
        },
    }

    resolved = resolve_profile(policy, profile=None)
    assert resolved["profile"] == "baseline"


def test_explicit_profile_overrides_default_profile():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "default_profile": "qa-lite",
        "profiles": {
            "baseline": {"rules": {"require_coverage": {"min_domains": 1}}},
            "qa-lite": {"rules": {"require_coverage": {"min_domains": 4}}},
            "strict-ci": {"rules": {"require_coverage": {"min_domains": 6}}},
        },
    }

    resolved = resolve_profile(policy, profile="strict-ci")
    assert resolved["profile"] == "strict-ci"
    assert resolved["rules"]["require_coverage"]["min_domains"] == 6


def test_missing_profile_errors_with_available_names():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "profiles": {"baseline": {"rules": {"require_coverage": {"min_domains": 1}}}},
    }

    with pytest.raises(ValueError) as e:
        resolve_profile(policy, profile="nope")

    msg = str(e.value).lower()
    assert "nope" in msg
    assert "baseline" in msg


def test_inheritance_child_overrides_parent_rules():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "profiles": {
            "baseline": {
                "rules": {
                    "require_coverage": {"min_domains": 1},
                    "require_evidence": {"min_items_per_domain": 0},
                    "min_coverage_items_per_domain": 0,
                    "forbid_empty_domains": False,
                }
            },
            "qa-lite": {
                "extends": "baseline",
                "rules": {
                    "require_coverage": {"min_domains": 4},
                    "require_evidence": {"min_items_per_domain": 1},
                },
            },
            "strict-ci": {
                "extends": "qa-lite",
                "rules": {"require_coverage": {"min_domains": 6}},
            },
        },
    }

    resolved = resolve_profile(policy, profile="strict-ci")
    assert resolved["rules"]["require_coverage"]["min_domains"] == 6
    # Inherited from qa-lite / baseline unless overridden
    assert resolved["rules"]["require_evidence"]["min_items_per_domain"] == 1
    assert resolved["chain"] == ["baseline", "qa-lite", "strict-ci"]


def test_inherited_profiles_merge_signals_policy_correctly():
    """
    v1.13+: signals policy should merge along inheritance chain.

    Contract we want to lock in:
      - start with policy-level signals, then apply each profile's signals in chain order
      - default_action: child overrides parent if provided
      - overrides: dict merge (child wins per key)
      - ignore: union/merge (deduped)
      - precedence between ignore/overrides/default is handled later (SignalsPolicy.action_for),
        but this resolver must carry the full merged config.
    """
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "signals": {
            "default_action": "info",
            "overrides": {"SIG-POLICY-ONLY": "warn"},
            "ignore": ["SIG-POLICY-IGNORE"],
        },
        "profiles": {
            "baseline": {
                "rules": {"require_coverage": {"min_domains": 1}},
                "signals": {
                    "default_action": "warn",
                    "overrides": {
                        "SIG-A": "warn",
                        "SIG-B": "error",
                    },
                    "ignore": ["SIG-BASELINE-IGNORE"],
                },
            },
            "qa-lite": {
                "extends": "baseline",
                "rules": {"require_coverage": {"min_domains": 2}},
                "signals": {
                    "default_action": "error",
                    "overrides": {
                        "SIG-B": "warn",  # override baseline
                        "SIG-C": "info",
                    },
                    "ignore": ["SIG-QA-IGNORE"],
                },
            },
        },
    }

    resolved = resolve_profile(policy, profile="qa-lite")

    assert resolved["chain"] == ["baseline", "qa-lite"]

    sigs = resolved["signals"]
    assert sigs["default_action"] == "error"

    # overrides merged with child-wins semantics
    expected_overrides = {
        "SIG-POLICY-ONLY": "warn",
        "SIG-A": "warn",
        "SIG-B": "warn",  # overridden by qa-lite
        "SIG-C": "info",
    }
    assert sigs["overrides"] == expected_overrides

    # ignore is merged/deduped. We assert as a set to avoid brittleness.
    assert set(sigs["ignore"]) == {"SIG-POLICY-IGNORE", "SIG-BASELINE-IGNORE", "SIG-QA-IGNORE"}


def test_inheritance_depth_limit_enforced():
    from course_engine.utils.policy import resolve_profile

    # baseline -> p2 -> p3 -> p4 -> p5 -> p6 (depth 6)
    policy = {
        "policy_version": 1,
        "profiles": {
            "baseline": {"rules": {"require_coverage": {"min_domains": 1}}},
            "p2": {"extends": "baseline", "rules": {}},
            "p3": {"extends": "p2", "rules": {}},
            "p4": {"extends": "p3", "rules": {}},
            "p5": {"extends": "p4", "rules": {}},
            "p6": {"extends": "p5", "rules": {}},
        },
    }

    with pytest.raises(ValueError) as e:
        resolve_profile(policy, profile="p6")

    msg = str(e.value).lower()
    assert "depth" in msg or "inherit" in msg


def test_inheritance_cycles_forbidden():
    from course_engine.utils.policy import resolve_profile

    policy = {
        "policy_version": 1,
        "profiles": {
            "a": {"extends": "b", "rules": {"require_coverage": {"min_domains": 1}}},
            "b": {"extends": "a", "rules": {}},
        },
    }

    with pytest.raises(ValueError) as e:
        resolve_profile(policy, profile="a")

    msg = str(e.value).lower()
    assert "cycle" in msg or "circular" in msg
