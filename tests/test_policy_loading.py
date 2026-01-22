# tests/test_policy_loading.py

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_yaml(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def test_loads_minimal_yaml_policy(tmp_path: Path):
    # Arrange
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 1
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
      require_evidence:
        min_items_per_domain: 0
      min_coverage_items_per_domain: 0
      forbid_empty_domains: false
""".lstrip(),
    )

    # Act
    from course_engine.utils.policy import load_policy_file

    policy = load_policy_file(p)

    # Assert
    assert policy["policy_version"] == 1
    assert "profiles" in policy
    assert "baseline" in policy["profiles"]
    assert policy["profiles"]["baseline"]["rules"]["require_coverage"]["min_domains"] == 1


def test_loads_minimal_json_policy(tmp_path: Path):
    # Arrange
    p = tmp_path / "policy.json"
    _write_json(
        p,
        {
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
        },
    )

    # Act
    from course_engine.utils.policy import load_policy_file

    policy = load_policy_file(p)

    # Assert
    assert policy["policy_version"] == 1
    assert "baseline" in policy["profiles"]


def test_loads_policy_with_signals_block(tmp_path: Path):
    """
    v1.13+: A policy/profile may include a `signals:` block.
    Loading should succeed as long as the block is valid.
    """
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 1
signals:
  default_action: info
  overrides:
    SIG-INTENT-001: warn
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
    signals:
      default_action: warn
      overrides:
        SIG-META-001: error
      ignore:
        - SIG-IGNORE-001
""".lstrip(),
    )

    from course_engine.utils.policy import load_policy_file

    policy = load_policy_file(p)

    assert policy["policy_version"] == 1

    # Top-level signals contract
    assert "signals" in policy
    assert policy["signals"]["default_action"] == "info"
    assert policy["signals"]["overrides"]["SIG-INTENT-001"] == "warn"

    # Profile-level signals contract
    assert "profiles" in policy
    assert "baseline" in policy["profiles"]
    baseline = policy["profiles"]["baseline"]
    assert "signals" in baseline
    assert baseline["signals"]["default_action"] == "warn"
    assert baseline["signals"]["overrides"]["SIG-META-001"] == "error"
    assert baseline["signals"]["ignore"] == ["SIG-IGNORE-001"]


def test_rejects_invalid_signal_action(tmp_path: Path):
    """
    v1.13+: Invalid signal actions should be rejected at load time.
    """
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 1
signals:
  default_action: explode
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
""".lstrip(),
    )

    from course_engine.utils.policy import load_policy_file

    with pytest.raises(ValueError) as e:
        load_policy_file(p)

    msg = str(e.value).lower()
    assert "default_action" in msg
    assert "ignore|info|warn|error" in msg


def test_rejects_missing_profiles(tmp_path: Path):
    p = tmp_path / "policy.yml"
    _write_yaml(p, "policy_version: 1\n")

    from course_engine.utils.policy import load_policy_file

    with pytest.raises(ValueError) as e:
        load_policy_file(p)

    assert "profiles" in str(e.value).lower()


def test_rejects_unsupported_policy_version(tmp_path: Path):
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 2
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
""".lstrip(),
    )

    from course_engine.utils.policy import load_policy_file

    with pytest.raises(ValueError) as e:
        load_policy_file(p)

    assert "policy_version" in str(e.value).lower()
    assert "1" in str(e.value)


def test_unknown_rule_key_is_error(tmp_path: Path):
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 1
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
      made_up_rule: true
""".lstrip(),
    )

    from course_engine.utils.policy import load_policy_file

    with pytest.raises(ValueError) as e:
        load_policy_file(p)

    msg = str(e.value).lower()
    assert "unknown" in msg or "unsupported" in msg
    assert "made_up_rule" in msg


def test_unknown_nested_rule_key_is_error(tmp_path: Path):
    p = tmp_path / "policy.yml"
    _write_yaml(
        p,
        """
policy_version: 1
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
        extra: 2
""".lstrip(),
    )

    from course_engine.utils.policy import load_policy_file

    with pytest.raises(ValueError) as e:
        load_policy_file(p)

    msg = str(e.value).lower()
    assert "unknown" in msg or "unsupported" in msg
    assert "extra" in msg
