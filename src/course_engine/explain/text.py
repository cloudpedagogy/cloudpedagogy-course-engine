# src/course_engine/explain/text.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _line(label: str, value: Any, indent: int = 0) -> str:
    pad = " " * indent
    v = "—" if value in (None, "", []) else str(value)
    return f"{pad}{label}: {v}"


def _bullet(items: List[str], indent: int = 2, max_items: int | None = None) -> List[str]:
    if not items:
        return [(" " * indent) + "—"]
    if max_items is not None:
        items = items[:max_items]
    return [(" " * indent) + f"- {x}" for x in items]


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _get_nested(d: Dict[str, Any], *path: str) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _truthy_dict(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict) and value:
        return value
    return None


def explain_payload_to_text(payload: Dict[str, Any]) -> str:
    """
    Render a human-readable explain report from the canonical explain JSON payload.

    Pure formatting only:
      - does not read files
      - does not build
      - does not validate
      - does not mutate payload
    """
    kind = payload.get("kind") or payload.get("type") or "explain"

    course = _as_dict(payload.get("course"))
    engine = _as_dict(payload.get("engine"))
    input_info = _as_dict(payload.get("input"))
    rendering = _as_dict(payload.get("rendering"))
    artefact_block = _as_dict(rendering.get("artefact"))  # manifest-backed artefact block (dist explain)

    sources = _as_dict(payload.get("sources"))
    source_files = sources.get("files") or []
    source_counts = _as_dict(sources.get("counts"))

    notes = payload.get("notes") or payload.get("warnings") or []
    errors = payload.get("errors") or []

    # Determine explain mode robustly
    input_type = input_info.get("type")
    is_artefact = bool(artefact_block) or (input_type == "dist_dir")
    explain_mode = "artefact (manifest-backed)" if is_artefact else "source (course.yml)"

    lines: List[str] = []
    lines.append("COURSE ENGINE EXPLAIN REPORT")
    lines.append("============================")
    lines.append("")
    lines.append(_line("Kind", kind))
    lines.append(_line("Mode", explain_mode))
    lines.append("")

    # 1. Course Identity
    lines.append("1. Course Identity")
    lines.append(_line("  Title", course.get("title")))
    lines.append(_line("  ID", course.get("id")))
    lines.append(_line("  Version", course.get("version")))
    if course.get("language") is not None:
        lines.append(_line("  Language", course.get("language")))
    lines.append("")

    # 2. Provenance
    lines.append("2. Provenance")
    lines.append(_line("  Engine version", engine.get("version")))
    lines.append(_line("  Built at (UTC)", engine.get("built_at_utc")))

    cmd = engine.get("command")
    if cmd:
        cmd_s = str(cmd)
        if len(cmd_s) > 140:
            cmd_s = cmd_s[:137] + "..."
        lines.append(_line("  Command", cmd_s))

    # Input path details (useful when relative paths confuse people)
    if input_info:
        lines.append(_line("  Input type", input_info.get("type")))
        lines.append(_line("  Input path", input_info.get("path_normalised") or input_info.get("path")))
    lines.append("")

    # 3. Artefact Summary (dist explain)
    if is_artefact:
        out = _as_dict(artefact_block.get("output"))
        b = _as_dict(artefact_block.get("builder"))
        inp = _as_dict(artefact_block.get("input"))

        lines.append("3. Artefact Summary")
        lines.append(_line("  Output format", out.get("format")))
        lines.append(_line("  Output dir", out.get("out_dir")))
        if artefact_block.get("manifest_version") is not None:
            lines.append(_line("  Manifest version", artefact_block.get("manifest_version")))
        if artefact_block.get("built_at_utc") is not None:
            lines.append(_line("  Artefact built at (UTC)", artefact_block.get("built_at_utc")))
        if artefact_block.get("refreshed_at_utc") is not None:
            lines.append(_line("  Artefact refreshed at (UTC)", artefact_block.get("refreshed_at_utc")))

        if b:
            lines.append("  Builder (from manifest):")
            lines.append(_line("    Name", b.get("name")))
            lines.append(_line("    Version", b.get("version")))
            lines.append(_line("    Python", b.get("python")))
            lines.append(_line("    Platform", b.get("platform")))

        if inp.get("course_yml"):
            lines.append(_line("  Source course.yml", inp.get("course_yml")))

        lines.append("")

    # 4. Outputs / Files
    lines.append("4. Outputs")

    # Prefer sources.counts.files (stable for dist explain)
    file_count = source_counts.get("files") if source_counts else None
    if file_count is None and isinstance(source_files, list):
        file_count = len(source_files)

    lines.append(_line("  File count", file_count))

    # Sample files: dist explain stores file objects with declared_path/resolved_path
    sample_paths: List[str] = []
    if isinstance(source_files, list) and source_files:
        for f in source_files:
            if isinstance(f, dict):
                # Prefer declared_path (stable relative path)
                dp = f.get("declared_path") or f.get("path") or f.get("resolved_path")
                if dp:
                    sample_paths.append(str(dp))
            else:
                sample_paths.append(str(f))

    if sample_paths:
        # Stabilise demo output: sort, then take first N
        sample_paths = sorted(sample_paths)[:12]
        lines.append("  Sample files:")
        lines.extend(_bullet(sample_paths, indent=4))
    lines.append("")

    # 5. Governance signals
    lines.append("5. Governance Signals")

    # framework_alignment may not exist; keep honest
    fw = payload.get("framework_alignment")
    if isinstance(fw, dict) and fw:
        lines.append("  Framework alignment:")
        lines.append(_line("    Framework", fw.get("framework_name")))
        domains = fw.get("domains") or []
        lines.append("    Domains:")
        if domains:
            lines.extend(_bullet([str(d) for d in domains], indent=6))
        else:
            lines.extend(_bullet([], indent=6))
        if fw.get("mapping_mode"):
            lines.append(_line("    Mapping mode", fw.get("mapping_mode")))
        if fw.get("notes") not in (None, ""):
            lines.append(_line("    Notes", fw.get("notes")))
    else:
        lines.append("  Framework alignment: none")

    cap = _as_dict(payload.get("capability_mapping"))
    present = cap.get("present")
    if present is True:
        lines.append("  Capability mapping: present")
    elif present is False:
        lines.append("  Capability mapping: none")
    else:
        # fallback for older shapes
        lines.append("  Capability mapping: " + ("present" if cap else "none"))
    lines.append("")

    # 6. Determinism note
    lines.append("6. Determinism")
    lines.append("  This report is derived from the canonical explain payload.")
    lines.append("  Non-determinism may occur only in runtime timestamps (e.g., built_at_utc).")
    lines.append("")

    # Errors/warnings (high value for governance legibility)
    if errors:
        lines.append("Errors:")
        if isinstance(errors, list):
            msgs = []
            for e in errors[:20]:
                if isinstance(e, dict):
                    code = e.get("code") or "ERROR"
                    msg = e.get("message") or ""
                    path = e.get("path")
                    if path:
                        msgs.append(f"{code}: {msg} ({path})")
                    else:
                        msgs.append(f"{code}: {msg}")
                else:
                    msgs.append(str(e))
            lines.extend(_bullet(msgs, indent=2))
        else:
            lines.append(f"  {errors}")
        lines.append("")

    if notes:
        lines.append("Warnings/Notes:")
        if isinstance(notes, list):
            lines.extend(_bullet([str(n) for n in notes][:20], indent=2))
        else:
            lines.append(f"  {notes}")
        lines.append("")

    return "\n".join(lines)
