# src/course_engine/pack/__init__.py

"""
Governance pack subsystem.

This module provides deterministic, facts-only packaging of curriculum
artefacts for quality assurance, audit, and archival workflows.
"""

from .packer import run_pack
from .profiles import PackItem, resolve_pack_profile
from .readme import render_pack_readme

__all__ = [
    "run_pack",
    "PackItem",
    "resolve_pack_profile",
    "render_pack_readme",
]
