from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    from importlib.metadata import version as pkg_version  # type: ignore
except Exception:  # pragma: no cover
    pkg_version = None  # type: ignore


MANIFEST_VERSION = "1.2.0"


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
    for p in sorted(out_dir.rglob("*")):
        if p.is_file():
            yield p


def get_course_engine_version(default: str = "unknown") -> str:
    if pkg_version is None:
        return default
    try:
        # IMPORTANT: distribution name must match your package name on install
        return pkg_version("course-engine")
    except Exception:
        return default


def _should_exclude(rel_path: str) -> bool:
    """
    Decide whether a file should be excluded from the manifest inventory.

    We exclude Quarto internals and common OS/LaTeX noise to keep manifests focused
    on meaningful course artefacts (e.g., index.pdf, _quarto.yml, index.qmd, _site outputs).
    """
    p = Path(rel_path)

    # Exclude any path that contains these directory segments
    EXCLUDE_DIRS = {".quarto"}

    # Exclude specific filenames
    EXCLUDE_FILES = {"manifest.json", ".DS_Store", ".gitignore"}

    # Exclude common LaTeX noise (optional but helpful)
    EXCLUDE_SUFFIXES = {".log", ".aux", ".out"}

    if any(part in EXCLUDE_DIRS for part in p.parts):
        return True

    if p.name in EXCLUDE_FILES:
        return True

    if p.suffix in EXCLUDE_SUFFIXES:
        return True

    return False


def build_file_inventory(
    out_dir: Path,
    *,
    include_hashes: bool = True,
    include_sizes: bool = True,
) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    files: list[dict[str, Any]] = []

    for file_path in _iter_files(out_dir):
        rel = _safe_relpath(file_path, out_dir)

        if _should_exclude(rel):
            continue

        entry: Dict[str, Any] = {"path": rel}

        if include_sizes:
            try:
                entry["bytes"] = file_path.stat().st_size
            except Exception:
                pass

        if include_hashes:
            try:
                entry["sha256"] = _sha256_file(file_path)
            except Exception:
                entry["sha256"] = None

        files.append(entry)

    return files


def _to_plain_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Convert common model/dict-like objects into a plain JSON-serializable dict.
    """
    if obj is None:
        return None

    # Pydantic v2
    if hasattr(obj, "model_dump"):
        out = obj.model_dump()
        return out if out else None

    # dict already
    if isinstance(obj, dict):
        return obj if obj else None

    # mapping-like
    try:
        out = dict(obj)
        return out if out else None
    except Exception:
        return None


def _framework_alignment_for_manifest(spec: Any) -> Optional[Dict[str, Any]]:
    """
    v1.6: Declared framework alignment metadata.

    This is the author's declared alignment intent (not coverage evidence).
    It should be recorded in the manifest for auditability, even when no
    lesson-level capability mapping exists.

    IMPORTANT: Depending on the CourseSpec model shape, framework_alignment may live at:
      - spec.framework_alignment
      - spec.course.framework_alignment
      - (dict forms) spec["framework_alignment"] / spec["course"]["framework_alignment"]
    """
    # 1) Try top-level attribute
    fa = getattr(spec, "framework_alignment", None)

    # 2) Try nested under spec.course
    if fa is None:
        course_obj = getattr(spec, "course", None)
        if course_obj is not None:
            fa = getattr(course_obj, "framework_alignment", None)

    # 3) Try dict-shaped spec
    if fa is None and isinstance(spec, dict):
        fa = spec.get("framework_alignment")
        if fa is None:
            course_dict = spec.get("course")
            if isinstance(course_dict, dict):
                fa = course_dict.get("framework_alignment")

    if fa is None:
        return None

    out = _to_plain_dict(fa)

    # Last resort: pick known common attributes if present
    if out is None:
        out = {
            "framework_name": getattr(fa, "framework_name", None),
            "domains": getattr(fa, "domains", None),
            "mapping_mode": getattr(fa, "mapping_mode", None),
            "notes": getattr(fa, "notes", None),
        }

    # Avoid writing empty/noisy blocks
    if not out:
        return None

    # Optional: normalize domains to plain list if it came back as a custom type
    if "domains" in out and out["domains"] is not None and not isinstance(out["domains"], (list, dict)):
        try:
            out["domains"] = list(out["domains"])
        except Exception:
            pass

    return out


def _capability_mapping_for_manifest(spec: Any) -> Optional[Dict[str, Any]]:
    """
    v1.1: Optional, informational capability mapping metadata.

    This is NOT enforced. We simply record it for auditability and reporting.
    """
    cap = getattr(spec, "capability_mapping", None)

    # dict-shaped spec fallback
    if cap is None and isinstance(spec, dict):
        cap = spec.get("capability_mapping")

    if cap is None:
        return None

    # If someone provided capability_mapping as a plain dict, pass it through
    cap_dict = _to_plain_dict(cap)
    if isinstance(cap, dict) and cap_dict is not None:
        # keep status consistent with existing behaviour if missing
        cap_dict.setdefault("status", "informational (not enforced)")
        return cap_dict

    domains_out: Dict[str, Any] = {}
    domains = getattr(cap, "domains", None) or {}
    for key, d in domains.items():
        domains_out[str(key)] = {
            "label": getattr(d, "label", None),
            "intent": getattr(d, "intent", None),
            "coverage": list(getattr(d, "coverage", []) or []),
            "evidence": list(getattr(d, "evidence", []) or []),
        }

    return {
        "framework": getattr(cap, "framework", None),
        "version": getattr(cap, "version", None),
        "domains": domains_out,
        "domains_declared": len(domains_out),
        "status": "informational (not enforced)",
    }


def _lesson_sources_for_manifest(spec: Any) -> Optional[Dict[str, Any]]:
    """
    v1.6 / manifest v1.2.0:
    Record lesson-level source provenance when lessons are authored via lesson.source.

    This is informational: it supports auditability and reproducible builds.
    """
    modules = getattr(spec, "modules", None) or []

    # dict-shaped spec fallback
    if not modules and isinstance(spec, dict):
        modules = spec.get("modules", []) or []

    lessons_out: list[dict[str, Any]] = []

    for module_item in modules:
        module_id = getattr(module_item, "id", None) if not isinstance(module_item, dict) else module_item.get("id")
        module_title = (
            getattr(module_item, "title", None) if not isinstance(module_item, dict) else module_item.get("title")
        )

        lessons = getattr(module_item, "lessons", None) or []
        if isinstance(module_item, dict):
            lessons = module_item.get("lessons", []) or []

        for lesson_item in lessons:
            src = (
                getattr(lesson_item, "source", None)
                if not isinstance(lesson_item, dict)
                else lesson_item.get("source")
            )
            if not src:
                continue

            lessons_out.append(
                {
                    "module_id": module_id,
                    "module_title": module_title,
                    "lesson_id": getattr(lesson_item, "id", None)
                    if not isinstance(lesson_item, dict)
                    else lesson_item.get("id"),
                    "lesson_title": getattr(lesson_item, "title", None)
                    if not isinstance(lesson_item, dict)
                    else lesson_item.get("title"),
                    "source": src,
                    "resolved_path": getattr(lesson_item, "source_resolved_path", None)
                    if not isinstance(lesson_item, dict)
                    else lesson_item.get("source_resolved_path"),
                    "sha256": getattr(lesson_item, "source_sha256", None)
                    if not isinstance(lesson_item, dict)
                    else lesson_item.get("source_sha256"),
                }
            )

    if not lessons_out:
        return None

    return {
        "count": len(lessons_out),
        "lessons": lessons_out,
        "status": "informational (not enforced)",
    }


def build_manifest(
    *,
    spec: Any,
    out_dir: Path,
    output_format: str,
    source_course_yml: Optional[Path] = None,
    include_hashes: bool = True,
    include_sizes: bool = True,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)

    course_id = getattr(spec, "id", None) or getattr(getattr(spec, "course", None), "id", None)
    course_title = getattr(spec, "title", None) or getattr(getattr(spec, "course", None), "title", None)
    course_version = getattr(spec, "version", None) or getattr(getattr(spec, "course", None), "version", None)

    spec_meta: Dict[str, Any] = {
        "id": course_id,
        "title": course_title,
        "version": course_version,
    }

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
        "files": build_file_inventory(out_dir, include_hashes=include_hashes, include_sizes=include_sizes),
    }

    # Persist declared framework alignment (metadata, not coverage evidence)
    fw_align = _framework_alignment_for_manifest(spec)
    if fw_align is not None:
        manifest["framework_alignment"] = fw_align

    cap_map = _capability_mapping_for_manifest(spec)
    if cap_map is not None:
        manifest["capability_mapping"] = cap_map

    lesson_sources = _lesson_sources_for_manifest(spec)
    if lesson_sources is not None:
        manifest["lesson_sources"] = lesson_sources

    return manifest


def write_manifest(
    *,
    spec: Any,
    out_dir: Path,
    output_format: str,
    source_course_yml: Optional[Path] = None,
    include_hashes: bool = True,
) -> Path:
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


def load_manifest(out_dir: Path) -> Dict[str, Any]:
    manifest_path = Path(out_dir) / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def refresh_manifest(
    out_dir: Path,
    *,
    include_hashes: bool = True,
    include_sizes: bool = True,
) -> Path:
    """
    Refresh file inventory (and optionally hashes) in an existing manifest.json.
    Does not require access to the original CourseSpec.
    """
    out_dir = Path(out_dir)
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Keep original built_at_utc; add a refresh marker
    manifest["refreshed_at_utc"] = _utc_now_iso()
    manifest["manifest_version"] = MANIFEST_VERSION

    # Update builder runtime info (useful when rendering happens later)
    manifest.setdefault("builder", {})
    manifest["builder"].update(
        {
            "name": "course-engine",
            "version": get_course_engine_version(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        }
    )

    manifest["files"] = build_file_inventory(out_dir, include_hashes=include_hashes, include_sizes=include_sizes)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def update_manifest_after_render(
    out_dir: Path,
    *,
    to: Optional[str] = None,
    input_file: Optional[str] = None,
    include_hashes: bool = True,
) -> Path:
    """
    Add a render record and refresh inventory after a successful render.
    If manifest doesn't exist, raises FileNotFoundError (by design).
    """
    out_dir = Path(out_dir)
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    render_block = {
        "rendered_at_utc": _utc_now_iso(),
        "to": to,
        "input_file": input_file,
    }

    manifest["render"] = render_block
    manifest["manifest_version"] = MANIFEST_VERSION

    # Refresh file inventory to include rendered outputs (e.g., index.pdf, _site/*)
    manifest["files"] = build_file_inventory(out_dir, include_hashes=include_hashes, include_sizes=True)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path
