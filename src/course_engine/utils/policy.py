from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# YAML is optional at import time, but required for .yml/.yaml policies.
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    # Python 3.9+
    from importlib import resources as importlib_resources
except Exception:  # pragma: no cover
    import importlib_resources  # type: ignore


PolicyDict = Dict[str, Any]

# ----------------------------
# Supported rule keys (v1.4+)
# ----------------------------

_ALLOWED_TOP_LEVEL_RULE_KEYS = {
    "require_coverage",
    "require_evidence",
    "min_coverage_items_per_domain",
    "forbid_empty_domains",
}

_ALLOWED_REQUIRE_COVERAGE_KEYS = {"min_domains"}
_ALLOWED_REQUIRE_EVIDENCE_KEYS = {"min_items_per_domain"}


# ----------------------------
# Public API
# ----------------------------

def load_policy_source(source: Optional[str]) -> PolicyDict:
    """
    Load a policy from either:
      - None -> default (preset:baseline)
      - 'preset:<name>' -> bundled preset policy
      - filesystem path -> YAML/JSON policy file

    Returns a validated policy dict.

    IMPORTANT:
      - We intentionally allow arbitrary top-level metadata keys (e.g., notes, owner).
      - We validate only the rule schema and required structural keys.
    """
    if source is None or str(source).strip() == "":
        return _load_preset_policy("baseline")

    source = str(source).strip()
    if source.startswith("preset:"):
        name = source.split("preset:", 1)[1].strip()
        if not name:
            raise ValueError(f"Invalid preset policy reference: {source!r}")
        return _load_preset_policy(name)

    # Treat as filesystem path
    return load_policy_file(Path(source))


def load_policy_file(path: Union[str, Path]) -> PolicyDict:
    """
    Load and validate a policy file (.yml/.yaml/.json).

    Enforces:
      - policy_version == 1
      - profiles exists and is a mapping
      - profiles[*].rules exists
      - only supported rule keys (including nested keys) are allowed

    Does NOT enforce a strict top-level schema: arbitrary metadata keys are allowed.
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"Policy file not found: {str(p)}")

    suffix = p.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise ValueError("YAML policy files require PyYAML. Install with: pip install pyyaml")
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    elif suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported policy file type: {suffix} (expected .yml/.yaml/.json)")

    if not isinstance(data, dict):
        raise ValueError("Policy file must parse to a mapping/object.")

    _validate_policy_dict(data)
    return data


def list_presets() -> List[str]:
    """List available bundled preset policy names (without extension)."""
    policies_dir = _preset_policies_dir()
    names: List[str] = []

    for entry in policies_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in {".yml", ".yaml"}:
            continue
        names.append(entry.stem)

    names.sort()
    return names


def list_profiles(policy: PolicyDict) -> List[str]:
    """Return profile names available in a policy."""
    profiles = policy.get("profiles", {})
    if not isinstance(profiles, dict):
        return []
    names = list(profiles.keys())
    names.sort()
    return names


def resolve_profile(policy: PolicyDict, profile: Optional[str] = None) -> PolicyDict:
    """
    Resolve a profile into a final set of rules, applying inheritance.

    Returns a dict with:
      - profile: selected profile name
      - chain: inheritance chain from base -> selected
      - rules: resolved rule dict
    """
    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("Policy 'profiles' must be a mapping.")

    selected = (profile or "").strip() or str(policy.get("default_profile") or "").strip() or "baseline"

    if selected not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        raise ValueError(f"Unknown profile '{selected}'. Available profiles: {available}")

    chain = _compute_inheritance_chain(profiles, selected, max_depth=5)
    resolved_rules: Dict[str, Any] = {}

    for name in chain:
        prof = profiles.get(name, {})
        rules = prof.get("rules", {})
        if rules is None:
            rules = {}
        if not isinstance(rules, dict):
            raise ValueError(f"Profile '{name}' rules must be a mapping.")
        resolved_rules = _merge_rules(resolved_rules, rules)

    return {
        "profile": selected,
        "chain": chain,
        "rules": resolved_rules,
    }


# ----------------------------
# Internal helpers
# ----------------------------

def _preset_policies_dir() -> Path:
    """
    Locate the bundled preset policies directory in the installed package.

    Expected layout:
      course_engine/presets/policies/*.yml
    """
    base = importlib_resources.files("course_engine")
    return Path(base.joinpath("presets").joinpath("policies"))


def _load_preset_policy(name: str) -> PolicyDict:
    policies_dir = _preset_policies_dir()
    yml = policies_dir / f"{name}.yml"
    yaml_path = policies_dir / f"{name}.yaml"

    if yml.exists():
        return load_policy_file(yml)
    if yaml_path.exists():
        return load_policy_file(yaml_path)

    available = ", ".join(list_presets())
    raise ValueError(f"Unknown preset policy '{name}'. Available presets: {available}")


def _validate_policy_dict(policy: PolicyDict) -> None:
    """
    Validate required structure + rule schema.

    We *intentionally allow* arbitrary top-level metadata keys:
      - policy_id, policy_name, owner, last_updated, notes, etc.
    """
    pv = policy.get("policy_version")
    if pv != 1:
        raise ValueError(f"Unsupported policy_version: {pv!r}. Expected 1.")

    profiles = policy.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Policy must define 'profiles' as a non-empty mapping.")

    for profile_name, profile_obj in profiles.items():
        if not isinstance(profile_obj, dict):
            raise ValueError(f"Profile '{profile_name}' must be a mapping/object.")

        rules = profile_obj.get("rules")
        if rules is None:
            raise ValueError(f"Profile '{profile_name}' must define 'rules'.")
        if not isinstance(rules, dict):
            raise ValueError(f"Profile '{profile_name}' rules must be a mapping/object.")

        _validate_rules(rules)


def _validate_rules(rules: Dict[str, Any]) -> None:
    """
    Enforce allowed rule keys and allowed nested keys.

    Supported keys:
      - require_coverage.min_domains (int)
      - require_evidence.min_items_per_domain (int)
      - min_coverage_items_per_domain (int)
      - forbid_empty_domains (bool)
    """
    for key in rules.keys():
        if key not in _ALLOWED_TOP_LEVEL_RULE_KEYS:
            raise ValueError(f"Unknown/unsupported rule key: {key}")

    if "require_coverage" in rules:
        rc = rules["require_coverage"]
        if not isinstance(rc, dict):
            raise ValueError("Rule 'require_coverage' must be a mapping/object.")
        for k in rc.keys():
            if k not in _ALLOWED_REQUIRE_COVERAGE_KEYS:
                raise ValueError(f"Unknown/unsupported rule key: require_coverage.{k}")

    if "require_evidence" in rules:
        re = rules["require_evidence"]
        if not isinstance(re, dict):
            raise ValueError("Rule 'require_evidence' must be a mapping/object.")
        for k in re.keys():
            if k not in _ALLOWED_REQUIRE_EVIDENCE_KEYS:
                raise ValueError(f"Unknown/unsupported rule key: require_evidence.{k}")


def _compute_inheritance_chain(
    profiles: Dict[str, Any],
    selected: str,
    max_depth: int = 5,
) -> List[str]:
    """Return inheritance chain from base -> selected."""
    chain: List[str] = []
    seen: set[str] = set()

    current = selected
    depth = 0

    while True:
        if current in seen:
            raise ValueError("Inheritance cycle detected in profiles.")
        seen.add(current)

        prof = profiles.get(current, {})
        if not isinstance(prof, dict):
            raise ValueError(f"Profile '{current}' must be a mapping/object.")

        parent = prof.get("extends")
        chain.append(current)

        if parent is None or str(parent).strip() == "":
            break

        parent = str(parent).strip()
        depth += 1
        if depth > max_depth:
            raise ValueError("Inheritance depth limit exceeded.")
        if parent not in profiles:
            raise ValueError(f"Profile '{current}' extends unknown parent '{parent}'.")

        current = parent

    chain.reverse()
    return chain


def _merge_rules(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two rules dicts. Child overrides parent.
    Nested merge only applies to require_coverage and require_evidence mappings.
    """
    merged: Dict[str, Any] = dict(base)

    for k, v in override.items():
        if k in {"require_coverage", "require_evidence"}:
            prev = merged.get(k, {})
            if not isinstance(prev, dict):
                prev = {}
            if v is None:
                v = {}
            if not isinstance(v, dict):
                raise ValueError(f"Rule '{k}' must be a mapping/object.")
            merged[k] = {**prev, **v}
        else:
            merged[k] = v

    return merged
