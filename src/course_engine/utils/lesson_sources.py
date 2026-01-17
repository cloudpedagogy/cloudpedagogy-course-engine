# src/course_engine/utils/lesson_sources.py

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def infer_title_from_md(md: str) -> Optional[str]:
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def normalise_path_str(p: str) -> str:
    """
    Deterministic normalisation:
      - POSIX slashes
      - remove leading "./"
      - do NOT resolve to absolute
    """
    s = Path(p).as_posix()
    while s.startswith("./"):
        s = s[2:]
    s = s.replace("//", "/")
    return s


@dataclass(frozen=True)
class LessonSourceResult:
    """
    Explain-friendly, non-throwing lesson source load result.
    """
    declared_path: str
    resolved_path: str
    resolved_path_normalised: str
    exists: bool
    bytes: Optional[int]
    hash_sha256: Optional[str]
    markdown: Optional[str]
    error: Optional[str]


def resolve_source_path(course_yml_path: Path, source: str) -> Path:
    """
    Resolve a lesson content source path relative to the course.yml folder,
    unless it is already absolute.
    """
    src = Path(source)
    course_root = course_yml_path.parent
    return src if src.is_absolute() else (course_root / src)


def load_lesson_source(course_yml_path: Path, source: str) -> LessonSourceResult:
    """
    Load a lesson markdown source file referenced by a content block `source:`.

    Returns a LessonSourceResult that never raises (unless arguments are invalid types).
    """
    declared = source
    resolved = resolve_source_path(course_yml_path, source)

    if not resolved.exists():
        return LessonSourceResult(
            declared_path=declared,
            resolved_path=str(resolved),
            resolved_path_normalised=normalise_path_str(str(resolved)),
            exists=False,
            bytes=None,
            hash_sha256=None,
            markdown=None,
            error="missing",
        )

    try:
        b = resolved.read_bytes()
        md = b.decode("utf-8")
        return LessonSourceResult(
            declared_path=declared,
            resolved_path=str(resolved),
            resolved_path_normalised=normalise_path_str(str(resolved)),
            exists=True,
            bytes=len(b),
            hash_sha256=sha256_bytes(b),
            markdown=md,
            error=None,
        )
    except Exception as e:
        return LessonSourceResult(
            declared_path=declared,
            resolved_path=str(resolved),
            resolved_path_normalised=normalise_path_str(str(resolved)),
            exists=True,
            bytes=None,
            hash_sha256=None,
            markdown=None,
            error=str(e),
        )
