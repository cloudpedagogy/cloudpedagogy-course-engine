from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

def run_pack(*, input_path: Path, out_dir: Path, engine_version: str, command: str) -> Dict[str, Any]:
    # Temporary stub — next commit will implement real pack generation
    return {
        "contents": {
            "summary_txt": False,
            "explain_txt": False,
            "explain_json": False,
            "manifest_json": False,
            "report_txt": False,
            "report_json": False,
            "validation_json": False,
        }
    }
