from __future__ import annotations
import os
from importlib import import_module
from typing import List

from .base import Plugin

def load_plugins() -> List[Plugin]:
    raw = os.getenv("COURSE_ENGINE_PLUGINS", "").strip()
    if not raw:
        return []

    plugins: List[Plugin] = []
    for mod_path in [p.strip() for p in raw.split(",") if p.strip()]:
        mod = import_module(mod_path)
        plugin = getattr(mod, "plugin", None)
        if plugin is None:
            raise RuntimeError(f"Plugin module {mod_path} has no `plugin` object.")
        plugins.append(plugin)
    return plugins
