"""
Governance snapshot generation for Course Engine v1.21+.

This module implements a **non-evaluative, deterministic snapshot**
of course state suitable for governance, CI, and diff-based review.

Design principles:
- facts only (no judgement)
- contract-stable output
- deterministic (timestamps aside)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union


CONTRACT_VERSION = "1"


def _utc_now_iso() -> str:
    # ISO 8601 with Z for UTC (diff-friendly, explicit)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_of_obj(obj: Any) -> str:
    """
    Compute a stable SHA256 hash of a Python object by:
    - canonical JSON serialisation
    - sorted keys
    """
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f) or {}


def _load_course_yml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load course.yml") from exc

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _presence(obj: Dict[str, Any], key: str) -> bool:
    return key in obj and obj[key] not in (None, {}, [])


def _norm_str(v: Any) -> str:
    """
    Safe normaliser for values that may be None or non-string.

    Used to satisfy type checkers and keep course id resolution robust.
    """
    if v is None:
        return ""
    s = v if isinstance(v, str) else str(v)
    return s.strip()


def _coalesce_course_id(d: Dict[str, Any]) -> str:
    """
    Best-effort course id resolution across schemas/eras.
    """
    # Common patterns seen across versions
    for k in ("course_id", "id"):
        cid = _norm_str(d.get(k))
        if cid:
            return cid

    # Nested course: { course: { id: ... } }
    course = d.get("course")
    if isinstance(course, dict):
        cid = _norm_str(course.get("id") or course.get("course_id"))
        if cid:
            return cid

    return "unknown"


def snapshot_from_course_yml(path: Path) -> Dict[str, Any]:
    """
    Build a governance snapshot from a source course.yml file.
    """
    course = _load_course_yml(path)
    course_id = _coalesce_course_id(course)

    # Extract known governance-relevant sections conservatively
    design_intent = course.get("design_intent")
    ai_scoping = course.get("ai_scoping")
    capability_mapping = course.get("capability_mapping")
    framework_alignment = course.get("framework_alignment")

    snapshot: Dict[str, Any] = {
        "mode": "snapshot",
        "contract_version": CONTRACT_VERSION,
        "generated_at_utc": None,  # filled by wrapper
        "input": {
            "kind": "source",
            "path": str(path),
            "course_id": course_id,
        },
        "versioning": {
            "course_engine_version": None,  # filled by wrapper
            "quarto_version": None,
            "pandoc_version": None,
        },
        "hashes": {
            "course_yml_hash": _sha256_of_obj(course),
            "design_intent_hash": _sha256_of_obj(design_intent) if design_intent is not None else None,
            "ai_scoping_hash": _sha256_of_obj(ai_scoping) if ai_scoping is not None else None,
            "policy_profile_hash": None,
        },
        "declared": {
            "framework_alignment_present": _presence(course, "framework_alignment"),
            "capability_mapping_present": _presence(course, "capability_mapping"),
            "design_intent_present": _presence(course, "design_intent"),
            "ai_scoping_present": _presence(course, "ai_scoping"),
        },
        "signals": {
            # Leave empty for MVP; can be populated later by a dedicated "absence signals" step.
            "absence": [],
            "notes": [],
        },
        "policy": {
            "policy_file": None,
            "profile": None,
            "effective_hash": None,
        },
        # Minimal declared payload slices (facts-only, small):
        "declared_payload": {
            "framework_alignment": framework_alignment if framework_alignment is not None else None,
            "capability_mapping_present": capability_mapping is not None,
        },
    }

    return snapshot


def snapshot_from_manifest(path: Path) -> Dict[str, Any]:
    """
    Build a governance snapshot from a dist artefact manifest.json file.
    """
    manifest = _load_json(path)

    # Try to infer course id from manifest fields
    course_id = "unknown"
    if isinstance(manifest.get("course"), dict):
        course_id = _coalesce_course_id(manifest.get("course") or {})
    if course_id == "unknown":
        # Some manifests might store id at top-level
        course_id = _coalesce_course_id(manifest)

    capability_mapping = manifest.get("capability_mapping")
    framework_alignment = manifest.get("framework_alignment")
    design_intent = manifest.get("design_intent")
    ai_scoping = manifest.get("ai_scoping")

    snapshot: Dict[str, Any] = {
        "mode": "snapshot",
        "contract_version": CONTRACT_VERSION,
        "generated_at_utc": None,  # filled by wrapper
        "input": {
            "kind": "artefact",
            "path": str(path),
            "course_id": course_id,
        },
        "versioning": {
            "course_engine_version": None,  # filled by wrapper
            "quarto_version": None,
            "pandoc_version": None,
        },
        "hashes": {
            "manifest_hash": _sha256_of_obj(manifest),
            "design_intent_hash": _sha256_of_obj(design_intent) if design_intent is not None else None,
            "ai_scoping_hash": _sha256_of_obj(ai_scoping) if ai_scoping is not None else None,
            "policy_profile_hash": None,
        },
        "declared": {
            "framework_alignment_present": framework_alignment not in (None, {}, []),
            "capability_mapping_present": capability_mapping not in (None, {}, []),
            "design_intent_present": design_intent not in (None, {}, []),
            "ai_scoping_present": ai_scoping not in (None, {}, []),
        },
        "signals": {
            "absence": [],
            "notes": [],
        },
        "policy": {
            "policy_file": None,
            "profile": None,
            "effective_hash": None,
        },
        "declared_payload": {
            "framework_alignment": framework_alignment if framework_alignment is not None else None,
            "capability_mapping_present": capability_mapping is not None,
        },
    }

    return snapshot


def snapshot(path: Path) -> Dict[str, Any]:
    """
    Dispatch snapshot generation based on input path.

    Supports:
      - course.yml (source)
      - manifest.json (artefact)
    """
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.is_dir():
        raise ValueError(f"Snapshot expects a file path (course.yml or manifest.json), got directory: {path}")

    name = path.name.lower()

    if name == "course.yml" or name.endswith(".yml") or name.endswith(".yaml"):
        return snapshot_from_course_yml(path)

    if name == "manifest.json":
        return snapshot_from_manifest(path)

    raise ValueError(f"Unsupported snapshot input: {path} (expected course.yml or manifest.json)")


def snapshot_from_path(
    path: Union[str, Path],
    engine_version: str,
    command: str,
    *,
    generated_at_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Public API expected by cli.py.

    - Resolves a path
    - Dispatches to snapshot()
    - Fills versioning + generated time fields
    """
    p = Path(path)

    payload = snapshot(p)

    payload["generated_at_utc"] = generated_at_utc or _utc_now_iso()

    # Versioning metadata (facts-only). Tool versions can be populated later if desired.
    versioning = payload.get("versioning") or {}
    versioning["course_engine_version"] = engine_version
    payload["versioning"] = versioning

    # Keep command for traceability (still facts-only; no evaluation)
    payload["command"] = command

    return payload


def snapshot_payload_to_text(payload: Dict[str, Any]) -> str:
    """
    Human-readable snapshot summary (one screen).
    Deterministic formatting; no judgement.
    """
    inp = payload.get("input") or {}
    declared = payload.get("declared") or {}
    hashes = payload.get("hashes") or {}
    versioning = payload.get("versioning") or {}

    lines = []
    lines.append("Course Engine snapshot")
    lines.append("")
    lines.append(f"Contract: v{payload.get('contract_version')}")
    lines.append(f"Generated: {payload.get('generated_at_utc') or '—'}")
    lines.append("")
    lines.append("Input")
    lines.append(f"  Kind: {inp.get('kind') or '—'}")
    lines.append(f"  Path: {inp.get('path') or '—'}")
    lines.append(f"  Course ID: {inp.get('course_id') or '—'}")
    lines.append("")
    lines.append("Declared sections (presence only)")
    lines.append(f"  framework_alignment: {'yes' if declared.get('framework_alignment_present') else 'no'}")
    lines.append(f"  capability_mapping: {'yes' if declared.get('capability_mapping_present') else 'no'}")
    lines.append(f"  design_intent: {'yes' if declared.get('design_intent_present') else 'no'}")
    lines.append(f"  ai_scoping: {'yes' if declared.get('ai_scoping_present') else 'no'}")
    lines.append("")
    lines.append("Versioning")
    lines.append(f"  course-engine: {versioning.get('course_engine_version') or '—'}")
    lines.append("")
    lines.append("Hashes (for diff/audit)")
    for k in sorted(hashes.keys()):
        v = hashes.get(k)
        lines.append(f"  {k}: {v if v is not None else '—'}")

    return "\n".join(lines) + "\n"
