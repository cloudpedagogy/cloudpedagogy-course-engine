# src/course_engine/explain/text.py
from __future__ import annotations

from typing import Any, Dict, List


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
    if isinstance(value, dict):
        return dict(value)  # shallow copy
    return {}


def _get_nested(d: Dict[str, Any], *path: str) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _truncate(s: str, n: int = 160) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    return s if len(s) <= n else s[: n - 1] + "…"


def explain_payload_to_text(payload: Dict[str, Any]) -> str:
    kind = payload.get("kind") or payload.get("type") or "explain"

    course = _as_dict(payload.get("course"))
    engine = _as_dict(payload.get("engine"))
    input_info = _as_dict(payload.get("input"))
    rendering = _as_dict(payload.get("rendering"))
    artefact_block = _as_dict(rendering.get("artefact"))

    sources = _as_dict(payload.get("sources"))
    source_files = sources.get("files") or []
    source_counts = _as_dict(sources.get("counts"))

    notes = payload.get("notes") or payload.get("warnings") or []
    errors = payload.get("errors") or []

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

    lines.append("1. Course Identity")
    lines.append(_line("  Title", course.get("title")))
    lines.append(_line("  ID", course.get("id")))
    lines.append(_line("  Version", course.get("version")))
    if course.get("language") is not None:
        lines.append(_line("  Language", course.get("language")))
    lines.append("")

    lines.append("2. Provenance")
    lines.append(_line("  Engine version", engine.get("version")))
    lines.append(_line("  Built at (UTC)", engine.get("built_at_utc")))

    cmd = engine.get("command")
    if cmd:
        cmd_s = str(cmd)
        if len(cmd_s) > 140:
            cmd_s = cmd_s[:137] + "..."
        lines.append(_line("  Command", cmd_s))

    if input_info:
        lines.append(_line("  Input type", input_info.get("type")))
        lines.append(_line("  Input path", input_info.get("path_normalised") or input_info.get("path")))
    lines.append("")

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

    lines.append("4. Outputs")

    file_count = source_counts.get("files") if source_counts else None
    if file_count is None and isinstance(source_files, list):
        file_count = len(source_files)
    lines.append(_line("  File count", file_count))

    sample_paths: List[str] = []
    if isinstance(source_files, list) and source_files:
        for f in source_files:
            if isinstance(f, dict):
                dp = f.get("declared_path") or f.get("path") or f.get("resolved_path")
                if dp:
                    sample_paths.append(str(dp))
            else:
                sample_paths.append(str(f))

    if sample_paths:
        sample_paths = sorted(sample_paths)[:12]
        lines.append("  Sample files:")
        lines.extend(_bullet(sample_paths, indent=4))
    lines.append("")

    lines.append("5. Governance Signals")

    fw_raw: Any = payload.get("framework_alignment")
    if not (isinstance(fw_raw, dict) and fw_raw):
        fw_raw = _get_nested(_as_dict(payload), "rendering", "artefact", "framework_alignment")
    fw = _as_dict(fw_raw)

    if fw:
        lines.append("  Framework alignment:")
        lines.append(_line("    Framework", fw.get("framework_name")))
        domains_any: Any = fw.get("domains") or []
        lines.append("    Domains:")
        if isinstance(domains_any, list) and domains_any:
            lines.extend(_bullet([str(d) for d in domains_any], indent=6))
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
        lines.append("  Capability mapping: " + ("present" if cap else "none"))

    di_raw: Any = payload.get("design_intent") or {}
    di = _as_dict(di_raw)
    if di.get("present") is True:
        lines.append("  Design intent: present")
        if di.get("hash_sha256"):
            lines.append(_line("    Hash (sha256)", di.get("hash_sha256")))
        if di.get("summary"):
            lines.append(_line("    Summary", _truncate(str(di.get("summary")))))
    else:
        lines.append("  Design intent: none")

    lines.append("")
    lines.append("6. Determinism")
    lines.append("  This report is derived from the canonical explain payload.")
    lines.append("  Non-determinism may occur only in runtime timestamps (e.g., built_at_utc).")
    lines.append("")

    if errors:
        lines.append("Errors:")
        if isinstance(errors, list):
            msgs: List[str] = []
            for e in errors[:20]:
                if isinstance(e, dict):
                    code = e.get("code") or "ERROR"
                    msg = e.get("message") or ""
                    path = e.get("path")
                    msgs.append(f"{code}: {msg} ({path})" if path else f"{code}: {msg}")
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


def explain_payload_to_summary(payload: Dict[str, Any]) -> str:
    """
    Render a one-screen, deterministic summary from the canonical explain payload.

    Pure formatting only:
      - no file reads
      - no build
      - no validation
      - no policy execution
    """
    lines: List[str] = []

    def add(s: str = "") -> None:
        lines.append(s)

    def present(v: Any) -> str:
        return "present" if v else "not present"

    course = _as_dict(payload.get("course"))
    engine = _as_dict(payload.get("engine"))
    input_info = _as_dict(payload.get("input"))
    rendering = _as_dict(payload.get("rendering"))
    artefact_block = _as_dict(rendering.get("artefact"))
    sources = _as_dict(payload.get("sources"))
    source_files = sources.get("files") or []
    source_counts = _as_dict(sources.get("counts"))
    errors = payload.get("errors") or []
    notes = payload.get("notes") or payload.get("warnings") or []

    input_type = input_info.get("type")
    is_artefact = bool(artefact_block) or (input_type == "dist_dir")
    mode = "artefact (manifest-backed)" if is_artefact else "source (course.yml)"

    add("Course Engine Summary")
    add(f"Mode: {mode}")
    add(f"Path: {input_info.get('path_normalised') or input_info.get('path') or '—'}")
    if engine.get("built_at_utc"):
        add(f"Generated at (UTC): {engine.get('built_at_utc')}")
    add("")

    add("Artefacts")
    add(f"- manifest.json: {present(is_artefact)}")

    src_course_yml = _get_nested(_as_dict(payload), "rendering", "artefact", "input", "course_yml")
    add(f"- course.yml: {present(src_course_yml or (not is_artefact))}")

    file_count = source_counts.get("files") if source_counts else None
    if file_count is None and isinstance(source_files, list):
        file_count = len(source_files)
    add(f"- file count: {file_count if file_count is not None else '—'}")
    add("")

    add("Declared metadata")
    add(f"- title: {course.get('title') or 'not declared'}")
    add(f"- id: {course.get('id') or 'not declared'}")
    add(f"- version: {course.get('version') or 'not declared'}")
    add(f"- language: {course.get('language') or 'not declared'}")
    add("")

    fw_raw: Any = payload.get("framework_alignment")
    if not (isinstance(fw_raw, dict) and fw_raw):
        fw_raw = _get_nested(_as_dict(payload), "rendering", "artefact", "framework_alignment")
    fw = _as_dict(fw_raw)

    add("Framework alignment")
    if fw:
        add(f"- framework: {fw.get('framework_name') or 'not declared'}")
        domains_any: Any = fw.get("domains") or []
        if isinstance(domains_any, list) and domains_any:
            add(f"- domains (declared): {', '.join([str(d) for d in domains_any])}")
        else:
            add("- domains (declared): none declared")
        if fw.get("mapping_mode"):
            add(f"- mapping mode: {fw.get('mapping_mode')}")
    else:
        add("- declared: no")
    add("")

    cap = _as_dict(payload.get("capability_mapping"))
    cap_present = cap.get("present")

    add("Capability mapping")
    if cap_present is True or (cap and cap_present is None):
        add("- present: yes")
    else:
        add("- present: no")
    add("")

    di_raw: Any = payload.get("design_intent") or {}
    di = _as_dict(di_raw)
    add("Design intent")
    add(f"- declared: {'yes' if di.get('present') is True else 'no'}")
    add("")

    sigs_any: Any = payload.get("signals") or _get_nested(_as_dict(payload), "rendering", "artefact", "signals") or []
    add("Governance signals (observed)")
    if isinstance(sigs_any, list) and sigs_any:
        dict_sigs = [x for x in sigs_any if isinstance(x, dict)]
        if dict_sigs:

            def _sid(d: Dict[str, Any]) -> str:
                return str(d.get("id") or d.get("signal") or d.get("code") or "")

            for d in sorted(dict_sigs, key=_sid)[:12]:
                sid = d.get("id") or d.get("signal") or d.get("code") or "—"
                label = d.get("label") or d.get("message") or ""
                label = _truncate(str(label), n=88)
                add(f"- {sid}: {label}" if label else f"- {sid}")
        else:
            sig_strs: List[str] = sorted([str(x) for x in sigs_any])[:12]
            for sig_str in sig_strs:
                add(f"- {sig_str}")
    else:
        add("- none")
    add("")

    missing: List[str] = []

    lifecycle = course.get("lifecycle")
    if lifecycle is None:
        missing.append("lifecycle metadata not declared")

    if di.get("present") is not True:
        missing.append("design intent not declared")

    # --- Robust ai_scoping detection (works across source + artefact payload shapes) ---
    ai_scoping_any: Any = payload.get("ai_scoping")
    if ai_scoping_any is None:
        ai_scoping_any = _get_nested(_as_dict(payload), "rendering", "artefact", "ai_scoping")
    ai_scoping_block = _as_dict(ai_scoping_any)

    declared_any: Any = payload.get("declared")
    if declared_any is None:
        declared_any = _get_nested(_as_dict(payload), "rendering", "artefact", "declared")
    declared_block = _as_dict(declared_any)

    ai_scoping_present = bool(ai_scoping_block) or (declared_block.get("ai_scoping_present") is True)

    if not ai_scoping_present:
        missing.append("ai_scoping not declared")
    # -------------------------------------------------------------------------------

    if not (cap_present is True or (cap and cap_present is None)):
        missing.append("capability mapping not declared")

    if not fw:
        missing.append("framework alignment not declared")

    add("Missing declarations (observed)")
    if missing:
        for item in missing:
            add(f"- {item}")
    else:
        add("- none")

    if errors or notes:
        add("")
        add("Notes")
        if isinstance(errors, list) and errors:
            add(f"- errors: {len(errors)}")
        elif errors:
            add("- errors: present")
        if isinstance(notes, list) and notes:
            add(f"- warnings/notes: {len(notes)}")
        elif notes:
            add("- warnings/notes: present")

    return "\n".join(lines)
