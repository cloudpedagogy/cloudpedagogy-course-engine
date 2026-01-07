from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..model import CourseSpec

@dataclass
class BuildContext:
    run_id: str = "local"

class Plugin(Protocol):
    name: str
    def pre_build(self, spec: CourseSpec, ctx: BuildContext) -> None: ...
    def post_build(self, spec: CourseSpec, ctx: BuildContext, out_dir: Path) -> None: ...
