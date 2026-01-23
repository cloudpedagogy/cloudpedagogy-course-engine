#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List


@dataclass
class LessonFile:
    path: Path
    title: str
    body: str


def indent_block(text: str, spaces: int) -> str:
    pad = " " * spaces
    # Ensure we always indent every line (including blank lines)
    return "\n".join(pad + line if line != "" else pad for line in text.splitlines())


def infer_title(md_text: str, fallback: str) -> str:
    """
    Uses first Markdown heading as title if present; otherwise fallback.
    """
    for line in md_text.splitlines():
        m = re.match(r"^\s*#\s+(.*)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback


def load_lessons(lessons_dir: Path) -> List[LessonFile]:
    if not lessons_dir.exists():
        raise FileNotFoundError(f"Lessons dir not found: {lessons_dir}")

    files = sorted(lessons_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No .md files found in: {lessons_dir}")

    lessons: List[LessonFile] = []
    for f in files:
        raw = f.read_text(encoding="utf-8").strip() + "\n"
        fallback = f.stem.replace("-", " ").replace("_", " ").title()
        title = infer_title(raw, fallback)
        lessons.append(LessonFile(path=f, title=title, body=raw))
    return lessons


def main(argv: List[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    if len(argv) != 2:
        print("Usage: python scripts/make_course_yml_from_lessons.py <lessons_dir> <out_course_yml>")
        print("Example: python scripts/make_course_yml_from_lessons.py demo/.../content/lessons demo/.../course.generated.yml")
        return 2

    lessons_dir = Path(argv[0]).resolve()
    out_path = Path(argv[1]).resolve()

    lessons = load_lessons(lessons_dir)

    # Build YAML for lessons content_blocks
    lessons_yaml_parts: List[str] = []
    for i, lesson in enumerate(lessons, start=1):
        lesson_id = f"l{i}"
        safe_title = lesson.title.replace('"', '\\"')

        lessons_yaml_parts.append(
            "\n".join(
                [
                    f"        - id: {lesson_id}",
                    f'          title: "{safe_title}"',
                    "          duration: 30",
                    "          tags: []",
                    "          prerequisites: []",
                    "          content_blocks:",
                    "            - type: \"markdown\"",
                    "              body: |",
                    indent_block(lesson.body.rstrip(), 16),
                    "",
                ]
            )
        )

    today = date.today().isoformat()

    yml = "\n".join(
        [
            'schema_version: "1.5"',
            "",
            "course:",
            '  id: "scenario-planning-environmental-scanning"',
            '  title: "Scenario Planning and Environmental Scanning"',
            '  subtitle: "Generated from split lesson .md files"',
            '  version: "0.1.0"',
            '  language: "en-GB"',
            f'  generated_at: "{today}"',
            "",
            "framework_alignment:",
            '  framework_name: "CloudPedagogy AI Capability Framework (2026 Edition)"',
            "  domains:",
            "    - Awareness",
            "    - Co-Agency",
            "    - Applied Practice & Innovation",
            "    - Ethics, Equity & Impact",
            "    - Decision-Making & Governance",
            "    - Reflection, Learning & Renewal",
            "",
            "outputs:",
            '  formats: ["html"]',
            '  theme: "cosmo"',
            "  toc: true",
            "",
            "structure:",
            "  modules:",
            '    - id: m1',
            '      title: "Scenario Planning and Environmental Scanning"',
            "      lessons:",
            "\n".join(lessons_yaml_parts),
            "",
        ]
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yml, encoding="utf-8")

    print(f"Wrote: {out_path}")
    print(f"Included {len(lessons)} lessons from: {lessons_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
