# src/course_engine/explain/artefact.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _utc_now_z() -> str:
    # Determinism policy allows engine.built_at_utc to vary.
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalise_path(p: Path) -> str:
    # Deterministic normalisation for reporting (no filesystem resolution side effects).
    return p.as_posix()


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)  # shallow copy
    return {}


def _truthy_present(block: Any) -> bool:
    """
    Determine presence for optional declared sections.

    We treat a section as "present" if:
      - block is a dict AND
      - block.present is True OR hash_sha256 is non-empty

    This avoids false positives from merely having the key in the manifest.
    """
    if not isinstance(block, dict):
        return False
    if block.get("present") is True:
        return True
    h = block.get("hash_sha256")
    return bool(h not in (None, ""))


def _count_lesson_qmd_files(manifest_files: List[Dict[str, Any]]) -> int:
    # Count generated lesson qmds in manifest (simple heuristic).
    n = 0
    for f in manifest_files or []:
        p = (f or {}).get("path")
        if not isinstance(p, str):
            continue
        if p.startswith("lessons/") and p.endswith(".qmd"):
            n += 1
    return n


def _sort_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic ordering for signal lists.
    Sort by (id, severity) to keep output stable for identical inputs.
    """

    def key(s: Dict[str, Any]) -> Tuple[str, str]:
        sid = s.get("id") or ""
        sev = s.get("severity") or ""
        return (sid, sev)

    return sorted(signals, key=key)


def explain_dist_dir(
    dist_dir: Path,
    *,
    engine_version: str,
    command: str,
) -> Dict[str, Any]:
    """
    Explain a built artefact directory (dist/<course>) into the stable explain JSON schema (v1.0+).

    This is explain-only:
      - read-only
      - no enforcement
      - no mutation

    Determinism:
      - deterministic except engine.built_at_utc
    """
    payload: Dict[str, Any] = {
        "explain_schema_version": "1.0",
        "engine": {
            "name": "cloudpedagogy-course-engine",
            "version": engine_version,
            "command": command,
            "built_at_utc": _utc_now_z(),
        },
        "input": {
            "type": "dist_dir",
            "path": str(dist_dir),
            "path_normalised": _normalise_path(Path(str(dist_dir))),
            "exists": dist_dir.exists(),
            "hash_sha256": None,
            "bytes": None,
        },
        "course": {
            "id": None,
            "version": None,
            "title": None,
            "subtitle": None,
            "description": None,
            "language": "en",
            "authors": [],
            "license": None,
            "tags": [],
            "metadata": {},
        },
        "structure": {
            "modules": [],
            "counts": {
                "modules": 0,
                "lessons": 0,
                "content_blocks": 0,
            },
        },
        "sources": {
            "files": [],
            "resolution": [],
            "counts": {
                "files": 0,
                "missing": 0,
            },
        },
        # surfaced governance metadata (manifest-backed when present)
        "framework_alignment": {},
        "capability_mapping": {
            "present": False,
            "summary": {},
            "details": None,
        },
        "design_intent": {
            "present": False,
            "hash_sha256": None,
            "summary": None,
        },
        # v1.13+ structural AI scoping (manifest-backed)
        "ai_scoping": {
            "present": False,
            "hash_sha256": None,
        },
        # Derived presence flags (must reflect actual manifest-backed state)
        "declared": {
            "framework_alignment_present": False,
            "capability_mapping_present": False,
            "design_intent_present": False,
            "ai_scoping_present": False,
        },
        "policies": {
            "active": [],
            "composed": {
                "layers": [],
                "resolved": {},
            },
            "hypothetical": {
                "would_fail": [],
                "would_warn": [],
            },
        },
        "rendering": {
            "profile": {
                "requested": None,
                "resolved": "default",
                "resolution_reason": "no profile specified; default applied",
            },
            "quarto": {
                "toc": True,
                "toc_depth": 2,
            },
        },
        # v1.13: absence signals (always present; copied from manifest if available)
        "signals": [],
        "warnings": [],
        "errors": [],
    }

    # Must be a directory that exists
    if not dist_dir.exists() or not dist_dir.is_dir():
        payload["errors"].append(
            {
                "code": "DIST_DIR_MISSING",
                "message": "dist directory not found or not a directory",
                "lesson_id": None,
                "path": str(dist_dir),
            }
        )
        return payload

    manifest_path = dist_dir / "manifest.json"
    if not manifest_path.exists():
        payload["errors"].append(
            {
                "code": "MANIFEST_MISSING",
                "message": "manifest.json not found in dist directory",
                "lesson_id": None,
                "path": str(manifest_path),
            }
        )
        return payload

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:  # keep explain resilient (no stack traces)
        payload["errors"].append(
            {
                "code": "MANIFEST_UNREADABLE",
                "message": f"could not read manifest.json: {e}",
                "lesson_id": None,
                "path": str(manifest_path),
            }
        )
        return payload

    # -------------------------
    # Populate from manifest
    # -------------------------
    course = _as_dict(manifest.get("course"))
    output = _as_dict(manifest.get("output"))
    builder = _as_dict(manifest.get("builder"))
    files = manifest.get("files") or []

    # Course identity
    payload["course"]["id"] = course.get("id")
    payload["course"]["version"] = course.get("version")
    payload["course"]["title"] = course.get("title")

    # Rendering / build info (informational)
    payload["rendering"]["artefact"] = {
        "manifest_version": manifest.get("manifest_version"),
        "built_at_utc": manifest.get("built_at_utc"),
        "refreshed_at_utc": manifest.get("refreshed_at_utc"),
        "builder": {
            "name": builder.get("name"),
            "version": builder.get("version"),
            "python": builder.get("python"),
            "platform": builder.get("platform"),
        },
        "output": {
            "format": output.get("format"),
            "out_dir": output.get("out_dir"),
        },
        "input": manifest.get("input") or {},
        "render": manifest.get("render") or None,
    }

    # Sources: map manifest file entries to explain file records
    out_files: List[Dict[str, Any]] = []
    missing = 0

    if isinstance(files, list):
        for f in files:
            if not isinstance(f, dict):
                continue
            rel_path = f.get("path")
            if not isinstance(rel_path, str):
                continue

            resolved_path = dist_dir / rel_path
            exists = resolved_path.exists()
            if not exists:
                missing += 1

            out_files.append(
                {
                    "declared_path": rel_path,
                    "resolved_path": str(resolved_path),
                    "path_normalised": _normalise_path(resolved_path),
                    "exists": bool(exists),
                    "bytes": f.get("bytes"),
                    "hash_sha256": f.get("sha256"),
                }
            )

    payload["sources"]["files"] = out_files
    payload["sources"]["counts"]["files"] = len(out_files)
    payload["sources"]["counts"]["missing"] = int(missing)

    # Structure counts (artefact-level best-effort)
    lesson_count = _count_lesson_qmd_files(files if isinstance(files, list) else [])
    payload["structure"]["counts"]["lessons"] = int(lesson_count)

    # Governance metadata copied from manifest (if present)
    fw = manifest.get("framework_alignment")
    if isinstance(fw, dict) and fw:
        payload["framework_alignment"] = dict(fw)

    di = manifest.get("design_intent")
    if isinstance(di, dict) and di:
        payload["design_intent"] = dict(di)

    ai = manifest.get("ai_scoping")
    if isinstance(ai, dict) and ai:
        payload["ai_scoping"] = dict(ai)

    # v1.13: signals copied from manifest (state-at-build-time)
    sigs = manifest.get("signals")
    if isinstance(sigs, list):
        sig_dicts = [s for s in sigs if isinstance(s, dict)]
        payload["signals"] = _sort_signals(sig_dicts)
    else:
        payload["signals"] = []

    # Capability mapping (if present in manifest)
    cap = manifest.get("capability_mapping")
    if cap:
        payload["capability_mapping"]["present"] = True
        payload["capability_mapping"]["summary"] = cap or {}
        payload["capability_mapping"]["details"] = None

    # -------------------------
    # Derived declared presence (MUST reflect manifest-backed truth)
    # -------------------------
    payload["declared"] = {
        "framework_alignment_present": bool(payload.get("framework_alignment")),
        "capability_mapping_present": bool(payload.get("capability_mapping", {}).get("present") is True),
        "design_intent_present": _truthy_present(payload.get("design_intent")),
        "ai_scoping_present": _truthy_present(payload.get("ai_scoping")),
    }

    return payload
