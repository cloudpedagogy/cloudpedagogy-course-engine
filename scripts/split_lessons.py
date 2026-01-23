#!/usr/bin/env python3
"""
Authoring utility.

Splits a Pandoc-generated Markdown course document into lesson-level files
for use with CloudPedagogy Course Engine.

- Not part of the runtime compiler
- Not imported by course_engine
- Intended for authors and maintainers

Supported lesson heading styles (H1):
  1) "# Lesson 1: Title"     (legacy numbered style)
  2) "# Title"              (plain H1 style; lessons are numbered by order)

Outputs:
  content/lessons/lesson-01-<slug>.md
  content/lessons/lesson-02-<slug>.md
  ...

Usage:
  python split_lessons.py <input.md> [output_dir] [--clean] [--dry-run] [--drop-h1] [--no-prefer-legacy-num]

Examples:
  python split_lessons.py content/scenario-planning-and-environmental-scanning.md content/lessons
  python split_lessons.py content/scenario-planning-and-environmental-scanning.md content/lessons --clean
  python split_lessons.py content/scenario-planning-and-environmental-scanning.md content/lessons --clean --drop-h1
  python split_lessons.py content/scenario-planning-and-environmental-scanning.md content/lessons --dry-run --drop-h1
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path


# Matches any H1 heading: "# Something"
H1_RE = re.compile(r"^(#)\s+(.+?)\s*$", re.MULTILINE)

# Matches legacy numbered pattern inside H1:
# "# Lesson 1: Title"
LEGACY_LESSON_RE = re.compile(r"^\s*Lesson\s+(\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE)


def slugify(text: str) -> str:
    """Convert a title into a filesystem-friendly slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()

    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")

    return text or "lesson"


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        print("Usage: python split_lessons.py <input.md> [output_dir] [--clean] [--dry-run] [--drop-h1] [--no-prefer-legacy-num]")
        print("Example: python split_lessons.py content/scenario-planning-and-environmental-scanning.md content/lessons --clean --drop-h1")
        raise SystemExit(2)

    input_path = Path(argv[1]).expanduser().resolve()

    output_dir: Path | None = None
    flags: set[str] = set()

    for a in argv[2:]:
        if a.startswith("--"):
            flags.add(a)
        elif output_dir is None:
            output_dir = Path(a).expanduser().resolve()
        else:
            print(f"ERROR: Unexpected argument: {a}")
            raise SystemExit(2)

    if output_dir is None:
        output_dir = Path.cwd() / "content" / "lessons"

    # flags
    clean = "--clean" in flags
    dry_run = "--dry-run" in flags
    drop_h1 = "--drop-h1" in flags
    prefer_legacy_num = "--no-prefer-legacy-num" not in flags  # default True

    unknown = [f for f in flags if f not in {"--clean", "--dry-run", "--drop-h1", "--no-prefer-legacy-num"}]
    if unknown:
        print(f"ERROR: Unknown flag(s): {', '.join(sorted(unknown))}")
        raise SystemExit(2)

    return {
        "input_path": input_path,
        "output_dir": output_dir,
        "clean": clean,
        "dry_run": dry_run,
        "drop_h1": drop_h1,
        "prefer_legacy_num": prefer_legacy_num,
    }


def _drop_first_h1_line(block: str) -> str:
    """
    Remove the first H1 line from a block, if it starts with an H1.

    This is useful when your Quarto page title is provided via front matter
    (or nav label), and you don't want the source content to repeat the title.
    """
    lines = block.splitlines()
    if not lines:
        return block

    # Find first non-empty line, and drop it if it is an H1.
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1

    if idx < len(lines) and lines[idx].lstrip().startswith("# "):
        # Drop that line, keep leading blank lines trimmed to at most one.
        new_lines = lines[:idx] + lines[idx + 1 :]
        # Normalize leading whitespace a bit (avoid huge blank top padding)
        while len(new_lines) > 0 and new_lines[0].strip() == "":
            new_lines.pop(0)
        return "\n".join(new_lines).rstrip() + "\n"

    return block


def split_on_h1(md: str, *, drop_h1: bool, prefer_legacy_num: bool) -> list[dict]:
    """
    Split markdown into blocks starting at each H1.

    Returns a list of dicts:
      {
        "num": lesson number (int),
        "title": extracted title (legacy or plain),
        "content": markdown block (optionally with H1 removed)
      }
    """
    matches = list(H1_RE.finditer(md))
    if not matches:
        raise ValueError("No H1 headings found. Expected lines like '# Title'.")

    lessons: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)

        raw_title = m.group(2).strip()

        legacy = LEGACY_LESSON_RE.match(raw_title)
        if legacy:
            legacy_num = int(legacy.group(1))
            title = legacy.group(2).strip()
            num = legacy_num if prefer_legacy_num else (i + 1)
        else:
            title = raw_title
            num = i + 1

        content_block = md[start:end].strip() + "\n"

        if drop_h1:
            content_block = _drop_first_h1_line(content_block)

        lessons.append({"num": num, "title": title, "content": content_block})

    return lessons


def clean_previous_outputs(output_dir: Path) -> int:
    """
    Remove existing lesson-??-*.md files in output_dir.
    Returns count removed.
    """
    removed = 0
    for p in output_dir.glob("lesson-??-*.md"):
        try:
            p.unlink()
            removed += 1
        except Exception:
            # best-effort; don't crash the run
            pass
    return removed


def main() -> int:
    args = parse_args(sys.argv)
    input_path: Path = args["input_path"]
    output_dir: Path = args["output_dir"]
    clean: bool = args["clean"]
    dry_run: bool = args["dry_run"]
    drop_h1: bool = args["drop_h1"]
    prefer_legacy_num: bool = args["prefer_legacy_num"]

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 2

    md = input_path.read_text(encoding="utf-8")

    try:
        lessons = split_on_h1(md, drop_h1=drop_h1, prefer_legacy_num=prefer_legacy_num)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    if clean and not dry_run:
        removed = clean_previous_outputs(output_dir)
        print(f"Cleaned {removed} existing lesson file(s) from: {output_dir}")

    created: list[Path] = []

    for lesson in lessons:
        num = int(lesson["num"])
        title = str(lesson["title"])
        slug = slugify(title)
        filename = f"lesson-{num:02d}-{slug}.md"
        out_path = output_dir / filename

        if dry_run:
            created.append(out_path)
            continue

        out_path.write_text(str(lesson["content"]), encoding="utf-8")
        created.append(out_path)

    print("Created lesson files:" if not dry_run else "Would create lesson files (dry run):")
    for p in created:
        try:
            rel = p.relative_to(Path.cwd())
            print(f"  - {rel}")
        except Exception:
            print(f"  - {p}")

    if drop_h1:
        print("\nNote: --drop-h1 was enabled, so each output file omits its leading H1 title line.")
        print("      (The page title should come from course.yml / Quarto front matter.)")

    if dry_run:
        print("\nDry run only: no files were written.")
    else:
        print("\nNext step:")
        print("  Update your course YAML to point each module item to these lesson files (one item per lesson).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
