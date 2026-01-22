# src/course_engine/utils/policy.py

from __future__ import annotations

import json
from importlib import resources as importlib_resources
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Dict, List, Optional, Union

# YAML is optional at import time, but required for .yml/.yaml policies.
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
# v1.13+: signal policy interpretation (optional)
# ----------------------------

_ALLOWED_SIGNAL_ACTIONS = {"ignore", "info", "warn", "error"}


# ----------------------------
# Public API
# ----------------------------

def load_policy_source(source: Optional[str]) -> PolicyDict:
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
    """
    Resolve a profile (with inheritance) into:
      - resolved structural rules
      - resolved signals policy (policy-level + inherited profile-level overrides)

    Returns a dict suitable for downstream validation/reporting:
      {
        "profile": "...",
        "chain": [...],
        "rules": {...},
        "signals": {
          "default_action": "info|warn|error|ignore",
          "overrides": { "SIG-...": "warn", ... },
          "ignore": ["SIG-...", ...]
        }
      }
    """
    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("Policy 'profiles' must be a mapping.")

    selected = (profile or "").strip() or str(policy.get("default_profile") or "").strip() or "baseline"

    if selected not in profiles:
        raise ValueError(f"Unknown profile '{selected}'.")

    chain = _compute_inheritance_chain(profiles, selected)

    resolved_rules: Dict[str, Any] = {}
    for name in chain:
        prof = profiles.get(name)
        if not isinstance(prof, dict):
            raise ValueError(f"Profile '{name}' must be a mapping/object.")
        rules = prof.get("rules", {}) or {}
        if not isinstance(rules, dict):
            raise ValueError(f"Profile '{name}'.rules must be a mapping/object.")
        resolved_rules = _merge_rules(resolved_rules, rules)

    resolved_signals = _resolve_signals_for_chain(policy=policy, profiles=profiles, chain=chain)

    return {
        "profile": selected,
        "chain": chain,
        "rules": resolved_rules,
        "signals": resolved_signals,
    }


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

    # optional: top-level signals block
    if "signals" in policy and policy["signals"] is not None:
        _validate_signals_block(policy["signals"], where="policy.signals")

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise ValueError(f"profiles.{profile_name} must be a mapping/object.")

        rules = profile.get("rules")
        if not isinstance(rules, dict):
            raise ValueError("Profile rules must be a mapping")
        _validate_rules(rules)

        # optional: per-profile signals block
        if "signals" in profile and profile["signals"] is not None:
            _validate_signals_block(profile["signals"], where=f"profiles.{profile_name}.signals")


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


def _validate_signals_block(block: Any, *, where: str) -> None:
    if not isinstance(block, dict):
        raise ValueError(f"{where} must be a mapping/object.")

    default_action = block.get("default_action", "info")
    if not isinstance(default_action, str) or default_action not in _ALLOWED_SIGNAL_ACTIONS:
        raise ValueError(f"{where}.default_action must be one of: ignore|info|warn|error")

    overrides = block.get("overrides", {})
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ValueError(f"{where}.overrides must be a mapping of {{SIGNAL_ID: action}}")

    for sid, action in overrides.items():
        if not isinstance(sid, str) or not sid.strip():
            raise ValueError(f"{where}.overrides keys must be non-empty strings (signal IDs)")
        if not isinstance(action, str) or action not in _ALLOWED_SIGNAL_ACTIONS:
            raise ValueError(f"{where}.overrides values must be one of: ignore|info|warn|error")

    ignore = block.get("ignore", [])
    if ignore is None:
        ignore = []
    if not isinstance(ignore, list) or any((not isinstance(x, str) or not x.strip()) for x in ignore):
        raise ValueError(f"{where}.ignore must be a list of signal ID strings")


def _normalise_signals_block(raw: Any) -> Dict[str, Any]:
    """
    Normalise a signals block into stable keys.

    Output shape (stable):
      {
        "default_action": "info|warn|error|ignore",
        "overrides": { "SIG-...": "warn", ... },
        "ignore": ["SIG-...", ...]
      }
    """
    if not isinstance(raw, dict):
        raw = {}

    default_action = raw.get("default_action", "info")
    if not isinstance(default_action, str) or default_action not in _ALLOWED_SIGNAL_ACTIONS:
        default_action = "info"

    overrides = raw.get("overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    ignore = raw.get("ignore") or []
    if not isinstance(ignore, list):
        ignore = []

    ignore_norm: List[str] = []
    seen_ignore: set[str] = set()
    for x in ignore:
        if isinstance(x, str) and x.strip():
            sid = x.strip()
            if sid not in seen_ignore:
                ignore_norm.append(sid)
                seen_ignore.add(sid)

    overrides_norm: Dict[str, str] = {}
    for sid, action in overrides.items():
        if not isinstance(sid, str) or not sid.strip():
            continue
        if not isinstance(action, str) or action not in _ALLOWED_SIGNAL_ACTIONS:
            continue
        overrides_norm[sid.strip()] = action

    return {
        "default_action": default_action,
        "overrides": overrides_norm,
        "ignore": ignore_norm,
    }


def _merge_signals_policy(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge signals policy with "override wins" semantics.
    - default_action: override if provided
    - overrides: dict merge (override wins per key)
    - ignore: union (dedupe, stable order: base first, then override)
    """
    merged_default = base.get("default_action", "info")
    merged_overrides = dict(base.get("overrides", {}) or {})
    merged_ignore = list(base.get("ignore", []) or [])

    # default_action
    if "default_action" in override and override.get("default_action"):
        merged_default = override["default_action"]

    # overrides (override wins per key)
    merged_overrides.update(override.get("overrides", {}) or {})

    # ignore (union, stable order)
    seen: set[str] = set(merged_ignore)
    for sid in override.get("ignore", []) or []:
        if sid not in seen:
            merged_ignore.append(sid)
            seen.add(sid)

    return {
        "default_action": merged_default,
        "overrides": merged_overrides,
        "ignore": merged_ignore,
    }


def _resolve_signals_for_chain(policy: PolicyDict, profiles: Dict[str, Any], chain: List[str]) -> Dict[str, Any]:
    """
    Resolve signals policy for a selected profile:
    start with policy-level signals, then apply each profile's signals in chain order.
    """
    resolved = _normalise_signals_block(policy.get("signals") or {})

    for name in chain:
        prof = profiles.get(name, {}) or {}
        if not isinstance(prof, dict):
            raise ValueError(f"Profile '{name}' must be a mapping/object.")
        if "signals" in prof and prof["signals"] is not None:
            prof_block = _normalise_signals_block(prof["signals"])
            resolved = _merge_signals_policy(resolved, prof_block)

    return resolved


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
        prof = profiles.get(current)
        if not isinstance(prof, dict):
            raise ValueError(f"Profile '{current}' must be a mapping/object.")

        parent = prof.get("extends")
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
