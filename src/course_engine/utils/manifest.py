from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    # Python 3.8+
    from importlib.metadata import version as pkg_version  # type: ignore
except Exception:  # pragma: no cover
    pkg_version = None  # type: ignore


MANIFEST_VERSION = "0.8.0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_relpath(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start))
    except Exception:
        return str(path)


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _iter_files(out_dir: Path) -> Iterable[Path]:
    # Deterministic ordering for stable manifests
    for p in sorted(out_dir.rglob("*")):
        if p.is_file():
            yield p


def get_course_engine_version(default: str = "unknown") -> str:
    """
    Return installed package version if available.
    Falls back to 'unknown' when running editable / not installed.
    """
    if pkg_version is None:
        return default
    try:
        return pkg_version("course-engine")
    except Exception:
        return default


def build_manifest(
    *,
    spec: Any,
    out_dir: Path,
    output_format: str,
    source_course_yml: Optional[Path] = None,
    include_hashes: bool = True,
    include_sizes: bool = True,
) -> Dict[str, Any]:
    """
    Build a manifest dict describing the build output.

    spec: your validated CourseSpec object (Pydantic / dataclass-ish)
    """
    out_dir = Path(out_dir)

    # Spec info (best-effort, avoids hard dependency on spec internals)
    course_id = getattr(spec, "id", None) or getattr(getattr(spec, "course", None), "id", None)
    course_title = getattr(spec, "title", None) or getattr(getattr(spec, "course", None), "title", None)
    course_version = getattr(spec, "version", None) or getattr(getattr(spec, "course", None), "version", None)

    # Serialize minimal spec metadata (avoid dumping full spec by default)
    spec_meta: Dict[str, Any] = {
        "id": course_id,
        "title": course_title,
        "version": course_version,
    }

    # Inventory generated files
    files: list[dict[str, Any]] = []
    for p in _iter_files(out_dir):
        # Exclude manifest itself (avoid self-hashing / churn)
        if p.name == "manifest.json":
            continue

        entry: Dict[str, Any] = {
            "path": _safe_relpath(p, out_dir),
        }
        if include_sizes:
            try:
                entry["bytes"] = p.stat().st_size
            except Exception:
                pass
        if include_hashes:
            try:
                entry["sha256"] = _sha256_file(p)
            except Exception:
                # If hashing fails for any reason, still include the file path
                entry["sha256"] = None

        files.append(entry)

    manifest: Dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "built_at_utc": _utc_now_iso(),
        "builder": {
            "name": "course-engine",
            "version": get_course_engine_version(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "input": {
            "course_yml": str(source_course_yml) if source_course_yml else None,
        },
        "course": spec_meta,
        "output": {
            "format": output_format,
            "out_dir": str(out_dir),
        },
        "files": files,
    }

    return manifest


def write_manifest(
    *,
    spec: Any,
    out_dir: Path,
    output_format: str,
    source_course_yml: Optional[Path] = None,
    include_hashes: bool = True,
) -> Path:
    """
    Write manifest.json into out_dir and return its path.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(
        spec=spec,
        out_dir=out_dir,
        output_format=output_format,
        source_course_yml=source_course_yml,
        include_hashes=include_hashes,
        include_sizes=True,
    )

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path
