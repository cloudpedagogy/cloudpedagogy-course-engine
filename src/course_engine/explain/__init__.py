"""
Explainability subsystem (v1.8+).

Public API:
  - explain_course_yml: explain a course.yml as stable JSON
    (deterministic except built_at_utc).
  - explain_dist_dir: explain a built dist/<course> directory
    (manifest-backed) as stable JSON.
"""

from __future__ import annotations

from .artefact import explain_dist_dir
from .course import explain_course_yml

__all__ = [
    "explain_course_yml",
    "explain_dist_dir",
]
