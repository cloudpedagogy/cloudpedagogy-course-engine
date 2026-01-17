# src/course_engine/explain/course.py

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..schema import validate_course_dict


EXPLAIN_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ExplainWarning:
    code: str
    message: str
    lesson_id: Optional[str] = None
    path: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "lesson_id": self.lesson_id,
            "path": self.path,
        }


@dataclass(frozen=True)
class ExplainError:
    code: str
    message: str
    path: Optional[str] = None
    lesson_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "lesson_id": self.lesson_id,
            "path": self.path,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm_path(p: str) -> str:
    # Deterministic normalisation: POSIX slashes, no leading "./"
    pp = Path(p)
    s = pp.as_posix()
    while s.startswith("./"):
        s = s[2:]
    s = s.replace("//", "/")
    return s


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _read_file_bytes(path: Path) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        data = path.read_bytes()
        return data, None
    except Exception as e:
        return None, str(e)


def _sorted_tags(tags: List[str]) -> List[str]:
    return sorted(tags, key=lambda x: (x or "").casefold())


def _sort_warnings(ws: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(w: Dict[str, Any]) -> Tuple[str, str, str]:
        code = w.get("code") or ""
        lesson_id = w.get("lesson_id") or "\uffff"
        path = w.get("path") or "\uffff"
        return (code, lesson_id, path)

    return sorted(ws, key=key)


def _sort_errors(es: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(e: Dict[str, Any]) -> Tuple[str, str, str]:
        code = e.get("code") or ""
        lesson_id = e.get("lesson_id") or "\uffff"
        path = e.get("path") or "\uffff"
        return (code, lesson_id, path)

    return sorted(es, key=key)


def _block_source_summary(block: Any) -> Dict[str, Any]:
    """
    Summarise a content block's source without embedding full content.

    v1.0:
      - inline bodies -> hash + bytes
      - file sources -> declared path only (resolved provenance comes later)
      - empty -> nulls
    """
    # Spec content blocks in your schema typically have .type and may have .body or .source
    body = getattr(block, "body", None)
    src = getattr(block, "source", None)

    if isinstance(src, str) and src.strip():
        # file-based source (declared)
        return {"kind": "file", "path": src, "hash_sha256": None, "bytes": None}

    if isinstance(body, str) and body != "":
        b = body.encode("utf-8")
        return {"kind": "inline", "path": None, "hash_sha256": _sha256_bytes(b), "bytes": len(b)}

    return {"kind": "empty", "path": None, "hash_sha256": None, "bytes": None}


def explain_course_yml(
    course_yml_path: str,
    engine_version: str,
    command: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Explain a course.yml into a governance-friendly JSON object.
    Deterministic except engine.built_at_utc.
    """
    path_arg = course_yml_path
    p = Path(course_yml_path)

    warnings: List[ExplainWarning] = []
    errors: List[ExplainError] = []

    # Input block
    input_obj: Dict[str, Any] = {
        "type": "course_yml",
        "path": path_arg,
        "path_normalised": _norm_path(path_arg),
        "exists": p.exists(),
        "hash_sha256": None,
        "bytes": None,
    }

    # Defaults required by schema
    course_obj: Dict[str, Any] = {
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
    }

    structure_obj: Dict[str, Any] = {
        "modules": [],
        "counts": {"modules": 0, "lessons": 0, "content_blocks": 0},
    }

    sources_obj: Dict[str, Any] = {
        "files": [],
        "resolution": [],
        "counts": {"files": 0, "missing": 0},
    }

    policies_obj: Dict[str, Any] = {
        "active": [],
        "composed": {"layers": [], "resolved": {}},
        "hypothetical": {"would_fail": [], "would_warn": []},
    }

    rendering_obj: Dict[str, Any] = {
        "profile": {
            "requested": None,
            "resolved": "default",
            "resolution_reason": "no profile specified; default applied",
        },
        # v1.0: always present with defaults
        "quarto": {"toc": True, "toc_depth": 2},
    }

    capability_mapping_obj: Dict[str, Any] = {"present": False, "summary": {}, "details": None}

    # Missing file: minimal explain with errors
    if not p.exists():
        errors.append(ExplainError(code="COURSE_YML_MISSING", message="course.yml not found", path=path_arg))
        return _finalise_explain(
            engine_version=engine_version,
            command=command,
            input_obj=input_obj,
            course_obj=course_obj,
            structure_obj=structure_obj,
            sources_obj=sources_obj,
            policies_obj=policies_obj,
            rendering_obj=rendering_obj,
            capability_mapping_obj=capability_mapping_obj,
            warnings=warnings,
            errors=errors,
        )

    data_bytes, read_err = _read_file_bytes(p)
    if data_bytes is None:
        errors.append(
            ExplainError(
                code="COURSE_YML_UNREADABLE",
                message=f"could not read course.yml: {read_err}",
                path=path_arg,
            )
        )
        return _finalise_explain(
            engine_version=engine_version,
            command=command,
            input_obj=input_obj,
            course_obj=course_obj,
            structure_obj=structure_obj,
            sources_obj=sources_obj,
            policies_obj=policies_obj,
            rendering_obj=rendering_obj,
            capability_mapping_obj=capability_mapping_obj,
            warnings=warnings,
            errors=errors,
        )

    input_obj["bytes"] = len(data_bytes)
    input_obj["hash_sha256"] = _sha256_bytes(data_bytes)

    # Parse YAML -> validate -> spec (canonical path)
    try:
        raw = yaml.safe_load(data_bytes.decode("utf-8"))
    except Exception as e:
        errors.append(ExplainError(code="COURSE_YML_PARSE_ERROR", message=str(e), path=path_arg))
        return _finalise_explain(
            engine_version=engine_version,
            command=command,
            input_obj=input_obj,
            course_obj=course_obj,
            structure_obj=structure_obj,
            sources_obj=sources_obj,
            policies_obj=policies_obj,
            rendering_obj=rendering_obj,
            capability_mapping_obj=capability_mapping_obj,
            warnings=warnings,
            errors=errors,
        )

    try:
        spec = validate_course_dict(raw, source_course_yml=p)
    except Exception as e:
        errors.append(ExplainError(code="COURSE_YML_INVALID", message=str(e), path=path_arg))
        return _finalise_explain(
            engine_version=engine_version,
            command=command,
            input_obj=input_obj,
            course_obj=course_obj,
            structure_obj=structure_obj,
            sources_obj=sources_obj,
            policies_obj=policies_obj,
            rendering_obj=rendering_obj,
            capability_mapping_obj=capability_mapping_obj,
            warnings=warnings,
            errors=errors,
        )

    # -------------------------
    # Extract course block (from validated spec)
    # -------------------------
    course_obj.update(
        {
            "id": getattr(spec, "id", None),
            "version": getattr(spec, "version", None),
            "title": getattr(spec, "title", None),
            "subtitle": getattr(spec, "subtitle", None),
            "description": getattr(spec, "description", None),
            "language": getattr(spec, "language", "en") or "en",
            "authors": list(getattr(spec, "authors", []) or []),
            "license": getattr(spec, "license", None),
            "tags": list(getattr(spec, "tags", []) or []),
            "metadata": dict(getattr(spec, "metadata", {}) or {}),
        }
    )
    course_obj["tags"] = _sorted_tags(course_obj.get("tags", []) or [])

    # -------------------------
    # Extract structure (author order)
    # -------------------------
    modules_out: List[Dict[str, Any]] = []
    modules = getattr(spec, "modules", None)

    lessons_count = 0
    blocks_count = 0

    if modules:
        for m in modules:
            lessons_out: List[Dict[str, Any]] = []
            lessons = getattr(m, "lessons", []) or []
            for lesson in lessons:
                cb = getattr(lesson, "content_blocks", []) or []
                content_blocks_out: List[Dict[str, Any]] = []
                for i, block in enumerate(cb):
                    blocks_count += 1
                    content_blocks_out.append(
                        {
                            "index": i,
                            "type": getattr(block, "type", None),
                            "source": _block_source_summary(block),
                        }
                    )

                lessons_out.append(
                    {
                        "id": getattr(lesson, "id", None),
                        "title": getattr(lesson, "title", None),
                        "nav_title": getattr(lesson, "lesson_nav_title", None),
                        "display_label": getattr(lesson, "display_label", None),
                        "duration": getattr(lesson, "duration", None),
                        "tags": _sorted_tags(list(getattr(lesson, "tags", []) or [])),
                        "prerequisites": list(getattr(lesson, "prerequisites", []) or []),
                        "content_blocks": content_blocks_out,
                    }
                )
                lessons_count += 1

            modules_out.append(
                {
                    "id": getattr(m, "id", None),
                    "title": getattr(m, "title", None),
                    "lessons": lessons_out,
                }
            )

    structure_obj["modules"] = modules_out
    structure_obj["counts"] = {
        "modules": len(modules_out),
        "lessons": lessons_count,
        "content_blocks": blocks_count,
    }

    # -------------------------
    # Rendering defaults (v1.0 always present)
    # Optionally override from spec outputs if present
    # -------------------------
    outputs = getattr(spec, "outputs", None)
    if outputs:
        # toc/toc_depth may exist depending on your outputs model
        toc_val = getattr(outputs, "toc", None)
        if isinstance(toc_val, bool):
            rendering_obj["quarto"]["toc"] = toc_val
        toc_depth_val = getattr(outputs, "toc_depth", None)
        if isinstance(toc_depth_val, int):
            rendering_obj["quarto"]["toc_depth"] = toc_depth_val

    # -------------------------
    # Sources (v1.8 MVP)
    # Keep present but minimal; wire lesson_sources provenance next increment.
    # -------------------------

    # capability mapping presence (informational)
    cap = getattr(spec, "capability_mapping", None)
    if cap is not None:
        capability_mapping_obj["present"] = True
        # If your model exposes summary-like fields, add them here deterministically.
        # Keep details null for now to avoid locking a premature format.

    return _finalise_explain(
        engine_version=engine_version,
        command=command,
        input_obj=input_obj,
        course_obj=course_obj,
        structure_obj=structure_obj,
        sources_obj=sources_obj,
        policies_obj=policies_obj,
        rendering_obj=rendering_obj,
        capability_mapping_obj=capability_mapping_obj,
        warnings=warnings,
        errors=errors,
    )


def _finalise_explain(
    engine_version: str,
    command: Optional[str],
    input_obj: Dict[str, Any],
    course_obj: Dict[str, Any],
    structure_obj: Dict[str, Any],
    sources_obj: Dict[str, Any],
    policies_obj: Dict[str, Any],
    rendering_obj: Dict[str, Any],
    capability_mapping_obj: Dict[str, Any],
    warnings: List[ExplainWarning],
    errors: List[ExplainError],
) -> Dict[str, Any]:
    out = {
        # Ordered top-level keys (for human diffs)
        "explain_schema_version": EXPLAIN_SCHEMA_VERSION,
        "engine": {
            "name": "cloudpedagogy-course-engine",
            "version": engine_version,
            "command": command,
            "built_at_utc": _utc_now_iso(),  # allowed non-determinism
        },
        "input": input_obj,
        "course": course_obj,
        "structure": structure_obj,
        "sources": sources_obj,
        "policies": policies_obj,
        "rendering": rendering_obj,
        "capability_mapping": capability_mapping_obj,
        "warnings": _sort_warnings([w.as_dict() for w in warnings]),
        "errors": _sort_errors([e.as_dict() for e in errors]),
    }
    return out
