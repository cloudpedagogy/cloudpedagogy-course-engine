# src/course_engine/explain/__init__.py

from __future__ import annotations

"""
Explainability subsystem (v1.8+).

Public API:
  - explain_course_yml: explain a course.yml as stable JSON (deterministic except built_at_utc).
"""

from .course import explain_course_yml

__all__ = ["explain_course_yml"]
