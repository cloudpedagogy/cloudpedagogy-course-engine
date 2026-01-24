# src/course_engine/pack/manifest.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

InputType = Literal["project", "artefact"]


def build_pack_manifest(
    *,
    engine_version: str,
    input_path: str,
    input_type: InputType,
    generated_at_utc: str,
    contents: Dict[str, bool],
    notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build pack_manifest.json (facts only; contract-like).

    Notes:
      - pack.input.path records the user-provided input path (which may be a parent OUT directory).
      - If the engine auto-resolves the effective artefact directory, packer may record it in notes
        (e.g., "resolved_input: /path/to/dist/<course-id>").
    """
    return {
        "pack": {
            "engine": {"name": "course-engine", "version": engine_version},
            "generated_at_utc": generated_at_utc,
            "input": {"path": input_path, "type": input_type},
        },
        "contents": {
            "readme_txt": bool(contents.get("readme_txt")),
            "summary_txt": bool(contents.get("summary_txt")),
            "explain_txt": bool(contents.get("explain_txt")),
            "explain_json": bool(contents.get("explain_json")),
            "manifest_json": bool(contents.get("manifest_json")),
            "report_txt": bool(contents.get("report_txt")),
            "report_json": bool(contents.get("report_json")),
            "validation_json": bool(contents.get("validation_json")),
        },
        "notes": notes or [],
    }
