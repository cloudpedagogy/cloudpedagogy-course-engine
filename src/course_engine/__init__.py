# src/course_engine/__init__.py

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    # Always report the installed distribution version
    __version__ = version("course-engine")
except PackageNotFoundError:  # pragma: no cover
    # Fallback for editable / dev edge cases
    __version__ = "0.0.0"

__all__ = ["__version__"]
