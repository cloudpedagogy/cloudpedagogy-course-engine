"""
Exporters for course-engine.

Each exporter turns a validated CourseSpec into a different output format
(e.g. Markdown, Quarto, PDF in future).
"""

from .markdown import build_markdown_package

__all__ = ["build_markdown_package"]
