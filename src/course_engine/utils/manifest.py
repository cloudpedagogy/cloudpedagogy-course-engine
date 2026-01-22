# src/course_engine/utils/manifest.py

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import yaml

try:
    from importlib.metadata import version as pkg_version  # type: ignore
except Exception:  # pragma: no cover
    pkg_version = None  # type: ignore

from .signals import compute_signals

MANIFEST_VERSION = "1.5.0"


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


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _iter_files(out_dir: Path) -> Iterable[Path]:
    for p in sorted(out_dir.rglob("*")):
        if p.is_file():
            yield p


def get_course_engine_version(default: str = "unknown") -> str:
    if pkg_version is None:
        return default
    try:
        return pkg_version("course-engine")
    except Exception:
        return default


def _should_exclude(rel_path: str) -> bool:
    p = Path(rel_path)

    EXCLUDE_DIRS = {".quarto"}
    EXCLUDE_FILES = {"manifest.json", ".DS_Store", ".gitignore"}
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
    if obj is None:
        return None

    if hasattr(obj, "model_dump"):
        out = obj.model_dump()
        return out if out else None

    if isinstance(obj, dict):
        return obj if obj else None

    try:
        out = dict(obj)
        return out if out else None
    except Exception:
        return None


def _framework_alignment_for_manifest(spec: Any) -> Optional[Dict[str, Any]]:
    fa = getattr(spec, "framework_alignment", None)

    if fa is None:
        course_obj = getattr(spec, "course", None)
        if course_obj is not None:
            fa = getattr(course_obj, "framework_alignment", None)

    if fa is None and isinstance(spec, dict):
        fa = spec.get("framework_alignment")
        if fa is None:
            course_dict = spec.get("course")
            if isinstance(course_dict, dict):
                fa = course_dict.get("framework_alignment")

    if fa is None:
        return None

    out = _to_plain_dict(fa)

    if out is None:
        out = {
            "framework_name": getattr(fa, "framework_name", None),
            "domains": getattr(fa, "domains", None),
            "mapping_mode": getattr(fa, "mapping_mode", None),
            "notes": getattr(fa, "notes", None),
        }

    if not out:
        return None

    if "domains" in out and out["domains"] is not None and not isinstance(out["domains"], (list, dict)):
        try:
            out["domains"] = list(out["domains"])
        except Exception:
            pass

    return out


def _capability_mapping_for_manifest(spec: Any) -> Optional[Dict[str, Any]]:
    cap = getattr(spec, "capability_mapping", None)
    if cap is None and isinstance(spec, dict):
        cap = spec.get("capability_mapping")
    if cap is None:
        return None

    cap_dict = _to_plain_dict(cap)
    if isinstance(cap, dict) and cap_dict is not None:
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
    modules = getattr(spec, "modules", None) or []
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
            src = getattr(lesson_item, "source", None) if not isinstance(lesson_item, dict) else lesson_item.get("source")
            if not src:
                continue

            lessons_out.append(
                {
                    "module_id": module_id,
                    "module_title": module_title,
                    "lesson_id": getattr(lesson_item, "id", None) if not isinstance(lesson_item, dict) else lesson_item.get("id"),
                    "lesson_title": getattr(lesson_item, "title", None) if not isinstance(lesson_item, dict) else lesson_item.get("title"),
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


def _design_intent_for_manifest(source_course_yml: Optional[Path]) -> Optional[Dict[str, Any]]:
    if not source_course_yml:
        return None

    p = Path(source_course_yml)
    if not p.exists():
        return None

    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(raw, dict):
        return None

    di = raw.get("design_intent")
    if not di:
        return {"present": False, "hash_sha256": None}

    try:
        di_json = json.dumps(di, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        di_json = str(di)

    block: Dict[str, Any] = {"present": True, "hash_sha256": _sha256_text(di_json)}

    if isinstance(di, dict):
        summary = di.get("summary")
        if isinstance(summary, str) and summary.strip():
            block["summary"] = summary.strip()

    return block


def _ai_scoping_for_manifest(source_course_yml: Optional[Path]) -> Optional[Dict[str, Any]]:
    """
    v1.13+ / manifest v1.5.0:
    Record AI scoping (presence + stable hash) from canonical course.yml.

    This is structural metadata only (no interpretation, no enforcement).
    """
    if not source_course_yml:
        return None

    p = Path(source_course_yml)
    if not p.exists():
        return None

    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(raw, dict):
        return None

    sc = raw.get("ai_scoping")
    if not sc:
        return {"present": False, "hash_sha256": None}

    try:
        sc_json = json.dumps(sc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        sc_json = str(sc)

    block: Dict[str, Any] = {"present": True, "hash_sha256": _sha256_text(sc_json)}

    if isinstance(sc, dict):
        summary = sc.get("scope_summary")
        if isinstance(summary, str) and summary.strip():
            block["scope_summary"] = summary.strip()

    return block


def _signals_for_manifest(spec: Any) -> list[dict[str, Any]]:
    try:
        signals = compute_signals(spec)
        return [s.to_dict() for s in signals]
    except Exception:
        return []


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

    spec_meta: Dict[str, Any] = {"id": course_id, "title": course_title, "version": course_version}

    manifest: Dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "built_at_utc": _utc_now_iso(),
        "builder": {
            "name": "course-engine",
            "version": get_course_engine_version(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "input": {"course_yml": str(source_course_yml) if source_course_yml else None},
        "course": spec_meta,
        "output": {"format": output_format, "out_dir": str(out_dir)},
        "signals": _signals_for_manifest(spec),
        "files": build_file_inventory(out_dir, include_hashes=include_hashes, include_sizes=include_sizes),
    }

    design_intent = _design_intent_for_manifest(source_course_yml)
    if design_intent is not None:
        manifest["design_intent"] = design_intent

    ai_scoping = _ai_scoping_for_manifest(source_course_yml)
    if ai_scoping is not None:
        manifest["ai_scoping"] = ai_scoping

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


def _normalise_manifest_version(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, int):
        return str(v)
    try:
        return str(v).strip()
    except Exception:
        return ""


def load_manifest(out_dir: Path) -> Dict[str, Any]:
    manifest_path = Path(out_dir) / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    if isinstance(data, dict):
        data["manifest_version"] = _normalise_manifest_version(data.get("manifest_version"))

    return data


def refresh_manifest(
    out_dir: Path,
    *,
    include_hashes: bool = True,
    include_sizes: bool = True,
) -> Path:
    out_dir = Path(out_dir)
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest["refreshed_at_utc"] = _utc_now_iso()
    manifest["manifest_version"] = MANIFEST_VERSION

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
    out_dir = Path(out_dir)
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json found in: {out_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest["render"] = {
        "rendered_at_utc": _utc_now_iso(),
        "to": to,
        "input_file": input_file,
    }
    manifest["manifest_version"] = MANIFEST_VERSION

    manifest["files"] = build_file_inventory(out_dir, include_hashes=include_hashes, include_sizes=True)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path
