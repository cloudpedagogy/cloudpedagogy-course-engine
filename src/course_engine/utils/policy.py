from __future__ import annotations

import json
from importlib import resources as importlib_resources
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Dict, List, Optional, Union

# YAML is optional at import time, but required for .yml/.yaml policies.
# mypy needs yaml to be typed as "module | None".
yaml: ModuleType | None
try:
    import yaml as _yaml  # type: ignore
    yaml = _yaml
except Exception:  # pragma: no cover
    yaml = None


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
    """
    if source is None or str(source).strip() == "":
        return _load_preset_policy("baseline")

    src = str(source).strip()
    if src.startswith("preset:"):
        name = src.split("preset:", 1)[1].strip()
        if not name:
            raise ValueError(f"Invalid preset policy reference: {src!r}")
        return _load_preset_policy(name)

    return load_policy_file(Path(src))


def load_policy_file(path: Union[str, Path]) -> PolicyDict:
    """
    Load and validate a policy file (.yml/.yaml/.json).
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
        raise ValueError(f"Unsupported policy file type: {suffix}")

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

        p = PurePosixPath(entry.name)
        if p.suffix.lower() not in {".yml", ".yaml"}:
            continue

        names.append(p.stem)

    names.sort()
    return names


def list_profiles(policy: PolicyDict) -> List[str]:
    profiles = policy.get("profiles", {})
    if not isinstance(profiles, dict):
        return []
    return sorted(profiles.keys())


def resolve_profile(policy: PolicyDict, profile: Optional[str] = None) -> PolicyDict:
    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("Policy 'profiles' must be a mapping.")

    selected = (profile or "").strip() or str(policy.get("default_profile") or "").strip() or "baseline"

    if selected not in profiles:
        raise ValueError(f"Unknown profile '{selected}'.")

    chain = _compute_inheritance_chain(profiles, selected)
    resolved_rules: Dict[str, Any] = {}

    for name in chain:
        rules = profiles[name].get("rules", {}) or {}
        resolved_rules = _merge_rules(resolved_rules, rules)

    return {"profile": selected, "chain": chain, "rules": resolved_rules}


# ----------------------------
# Internal helpers
# ----------------------------

def _preset_policies_dir():
    return importlib_resources.files("course_engine").joinpath("presets", "policies")


def _load_preset_policy(name: str) -> PolicyDict:
    policies_dir = _preset_policies_dir()
    for suffix in (".yml", ".yaml"):
        path = policies_dir.joinpath(f"{name}{suffix}")
        if path.is_file():
            return _load_policy_from_text(path.read_text(encoding="utf-8"), suffix=suffix)

    raise ValueError(f"Unknown preset policy '{name}'. Available: {', '.join(list_presets())}")


def _load_policy_from_text(text: str, *, suffix: str) -> PolicyDict:
    if suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise ValueError("YAML support requires PyYAML.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Policy must parse to a mapping/object.")

    _validate_policy_dict(data)
    return data


def _validate_policy_dict(policy: PolicyDict) -> None:
    if policy.get("policy_version") != 1:
        raise ValueError("policy_version must be 1")

    profiles = policy.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Policy must define non-empty 'profiles'")

    for profile in profiles.values():
        rules = profile.get("rules")
        if not isinstance(rules, dict):
            raise ValueError("Profile rules must be a mapping")
        _validate_rules(rules)


def _validate_rules(rules: Dict[str, Any]) -> None:
    for key in rules:
        if key not in _ALLOWED_TOP_LEVEL_RULE_KEYS:
            raise ValueError(f"Unsupported rule key: {key}")

    if "require_coverage" in rules:
        for k in rules["require_coverage"]:
            if k not in _ALLOWED_REQUIRE_COVERAGE_KEYS:
                raise ValueError(f"Unsupported require_coverage key: {k}")

    if "require_evidence" in rules:
        for k in rules["require_evidence"]:
            if k not in _ALLOWED_REQUIRE_EVIDENCE_KEYS:
                raise ValueError(f"Unsupported require_evidence key: {k}")


def _compute_inheritance_chain(
    profiles: Dict[str, Any],
    selected: str,
    max_depth: int = 5,
) -> List[str]:
    chain: List[str] = []
    seen: set[str] = set()

    current = selected
    depth = 0

    while True:
        if current in seen:
            raise ValueError("Inheritance cycle detected")
        seen.add(current)

        chain.append(current)
        parent = profiles[current].get("extends")
        if not parent:
            break

        depth += 1
        if depth > max_depth:
            raise ValueError("Inheritance depth exceeded")

        if parent not in profiles:
            raise ValueError(f"Unknown parent profile '{parent}'")

        current = parent

    chain.reverse()
    return chain


def _merge_rules(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)

    for k, v in override.items():
        if k in {"require_coverage", "require_evidence"}:
            merged[k] = {**merged.get(k, {}), **(v or {})}
        else:
            merged[k] = v

    return merged
