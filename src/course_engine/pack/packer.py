# src/course_engine/pack/packer.py
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Tuple

from ..explain import explain_course_yml
from ..explain.artefact import explain_dist_dir
from ..explain.text import explain_payload_to_summary, explain_payload_to_text
from ..utils.fileops import write_text
from ..utils.manifest import load_manifest
from ..utils.reporting import build_capability_report, report_to_json, report_to_text

from .manifest import build_pack_manifest

InputType = Literal["project", "artefact"]


class PackInputError(ValueError):
    """Raised when pack input cannot be resolved to a valid project or artefact."""


def _find_artefact_candidates(parent: Path) -> list[Path]:
    """
    Return direct child directories that contain manifest.json.
    Sorted for determinism.
    """
    candidates: list[Path] = []
    for child in sorted(parent.iterdir()):
        if child.is_dir() and (child / "manifest.json").is_file():
            candidates.append(child)
    return candidates


def _detect_input(input_path: Path) -> Tuple[InputType, Path]:
    """
    Returns (input_type, resolved_path)

    - artefact: a directory containing manifest.json
               OR a parent directory containing exactly one child dir with manifest.json
    - project:  a directory containing course.yml OR a direct path to course.yml
    """
    p = input_path

    if p.is_dir():
        # 1) Direct artefact dir
        if (p / "manifest.json").is_file():
            return "artefact", p

        # 2) Project dir
        if (p / "course.yml").is_file():
            return "project", p / "course.yml"

        # 3) Parent OUT dir auto-detection: exactly one child artefact dir
        candidates = _find_artefact_candidates(p)
        if len(candidates) == 1:
            return "artefact", candidates[0]

        if len(candidates) > 1:
            rendered = "\n".join(f"  - {c}" for c in candidates)
            raise PackInputError(
                f"Input directory not recognised: {p}\n"
                "This directory contains multiple artefact candidates (each has manifest.json):\n"
                f"{rendered}\n"
                "Tip: pass one of the candidate directories explicitly (e.g. dist/<course-id>)."
            )

        # 4) Nothing matched
        raise PackInputError(
            f"Input directory not recognised: {p}\n"
            "Expected either:\n"
            "  - dist/<course-id> containing manifest.json, or\n"
            "  - a parent OUT directory containing exactly one dist/<course-id>/manifest.json, or\n"
            "  - a course project folder containing course.yml"
        )

    # File path
    if p.is_file() and p.name == "course.yml":
        return "project", p

    raise PackInputError(
        f"Input path not recognised: {p}\n"
        "Pass either:\n"
        "  - a path to course.yml, or\n"
        "  - a course project folder containing course.yml, or\n"
        "  - a dist/<course-id> folder containing manifest.json, or\n"
        "  - a parent OUT folder containing exactly one dist/<course-id>/manifest.json"
    )


def run_pack(
    *,
    input_path: Path,
    out_dir: Path,
    engine_version: str,
    command: str,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    contents: Dict[str, bool] = {
        "summary_txt": False,
        "explain_txt": False,
        "explain_json": False,
        "manifest_json": False,
        "report_txt": False,
        "report_json": False,
        "validation_json": False,  # v1.16 MVP: not generated yet
    }
    notes: list[str] = []

    input_type, resolved = _detect_input(input_path)

    # Record resolution (especially useful when input_path is a parent OUT dir)
    if resolved != input_path:
        notes.append(f"resolved_input: {resolved}")

    # Explain payload
    if input_type == "artefact":
        payload = explain_dist_dir(dist_dir=resolved, engine_version=engine_version, command=command)
    else:
        payload = explain_course_yml(course_yml_path=str(resolved), engine_version=engine_version, command=command)

    # Write explain outputs
    explain_json_path = out_dir / "explain.json"
    explain_txt_path = out_dir / "explain.txt"
    summary_txt_path = out_dir / "summary.txt"

    write_text(explain_json_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    contents["explain_json"] = True

    write_text(explain_txt_path, explain_payload_to_text(payload) + "\n")
    contents["explain_txt"] = True

    write_text(summary_txt_path, explain_payload_to_summary(payload) + "\n")
    contents["summary_txt"] = True

    # Copy manifest.json if present (artefact inputs)
    if input_type == "artefact":
        src_manifest = resolved / "manifest.json"
        if src_manifest.is_file():
            shutil.copy2(src_manifest, out_dir / "manifest.json")
            contents["manifest_json"] = True

            # Optional report if capability mapping exists
            try:
                m = load_manifest(resolved)
            except Exception as e:
                notes.append(f"manifest_load_failed: {type(e).__name__}")
                m = None

            if isinstance(m, dict) and m.get("capability_mapping"):
                rep = build_capability_report(m)

                report_txt_path = out_dir / "report.txt"
                report_json_path = out_dir / "report.json"

                write_text(report_txt_path, report_to_text(rep, verbose=False))
                contents["report_txt"] = True

                write_text(report_json_path, report_to_json(rep))
                contents["report_json"] = True

    # Pack manifest (always)
    generated_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    pack_manifest = build_pack_manifest(
        engine_version=engine_version,
        input_path=str(input_path),
        input_type=input_type,
        generated_at_utc=generated_at_utc,
        contents=contents,
        notes=notes,
    )
    write_text(out_dir / "pack_manifest.json", json.dumps(pack_manifest, indent=2, ensure_ascii=False) + "\n")

    return {
        "contents": contents,
        "notes": notes,
    }
