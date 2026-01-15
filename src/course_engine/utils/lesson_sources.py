from __future__ import annotations
from pathlib import Path
import hashlib

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def infer_title_from_md(md: str) -> str | None:
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None

def load_lesson_source(course_yml_path: Path, source: str) -> tuple[str, str, str]:
    """
    Returns (markdown_body, sha256, resolved_path_str)
    """
    src = Path(source)
    course_root = course_yml_path.parent
    resolved = src if src.is_absolute() else (course_root / src)
    md = resolved.read_text(encoding="utf-8")
    return md, sha256_text(md), str(resolved)
