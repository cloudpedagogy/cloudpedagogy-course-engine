from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now_z() -> str:
    # v1.8 determinism policy allows engine.built_at_utc to vary.
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalise_path(p: Path) -> str:
    # Deterministic normalisation for reporting (no filesystem resolution side effects).
    return p.as_posix()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def explain_dist_dir(
    dist_dir: Path,
    *,
    engine_version: str,
    command: str,
) -> Dict[str, Any]:
    """
    Explain a built artefact directory (dist/<course>) into the stable explain JSON schema (v1.0).

    This is explain-only:
      - read-only
      - no enforcement
      - no mutation

    Determinism:
      - deterministic except engine.built_at_utc
    """
    # Top-level output is deliberately ordered.
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
        "capability_mapping": {
            "present": False,
            "summary": {},
            "details": None,
        },
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
        manifest = _read_json(manifest_path)
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
    course = manifest.get("course") or {}
    output = manifest.get("output") or {}
    builder = manifest.get("builder") or {}
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
    lesson_count = _count_lesson_qmd_files(files)
    payload["structure"]["counts"]["lessons"] = int(lesson_count)
    payload["structure"]["counts"]["modules"] = 0
    payload["structure"]["counts"]["content_blocks"] = 0

    # Capability mapping / framework alignment (if present in manifest)
    if manifest.get("capability_mapping"):
        payload["capability_mapping"]["present"] = True
        payload["capability_mapping"]["summary"] = manifest.get("capability_mapping") or {}
        payload["capability_mapping"]["details"] = None

    return payload
