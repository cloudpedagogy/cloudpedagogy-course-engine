# src/course_engine/utils/preflight.py

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class PrereqError(RuntimeError):
    """Raised when an external prerequisite is missing."""


# Cache PDF preflight result per process to avoid re-checking repeatedly.
_PDF_PREFLIGHT_OK: Optional[bool] = None


def has_quarto() -> bool:
    """Return True if Quarto is available on PATH."""
    return shutil.which("quarto") is not None


def get_quarto_path() -> Optional[str]:
    """Return resolved path to `quarto` if found, else None."""
    return shutil.which("quarto")


def get_pandoc_path() -> Optional[str]:
    """Return resolved path to `pandoc` if found, else None."""
    return shutil.which("pandoc")


def require_quarto() -> None:
    """Ensure Quarto is installed and on PATH."""
    if not has_quarto():
        raise PrereqError(
            "Quarto is required but was not found on your PATH.\n\n"
            "Install Quarto from https://quarto.org/ and try again."
        )


def require_pdf_toolchain() -> None:
    """
    Ensure PDF rendering works by doing a tiny Quarto->PDF smoke test.

    This avoids fragile parsing of `quarto check` output.
    """
    global _PDF_PREFLIGHT_OK

    if _PDF_PREFLIGHT_OK is True:
        return

    require_quarto()

    with tempfile.TemporaryDirectory(prefix="course-engine-pdf-check-") as td:
        tdir = Path(td)

        # Minimal Quarto document
        (tdir / "index.qmd").write_text(
            "# PDF preflight\n\nIf you can read this, PDF rendering works.\n",
            encoding="utf-8",
        )

        # Minimal config forcing PDF format
        (tdir / "_quarto.yml").write_text(
            "project:\n"
            "  type: default\n"
            "\n"
            "format:\n"
            "  pdf:\n"
            "    toc: false\n"
            "\n"
            "execute:\n"
            "  echo: false\n",
            encoding="utf-8",
        )

        # Run quarto render in that directory
        cmd = ["quarto", "render", str(tdir)]
        completed = subprocess.run(cmd, capture_output=True, text=True)

        if completed.returncode != 0:
            _PDF_PREFLIGHT_OK = False

            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()

            msg = (
                "PDF output requires a LaTeX toolchain.\n\n"
                "Recommended fix (one-time):\n"
                "  quarto install tinytex\n\n"
                "Then retry your command.\n"
            )

            details = stderr if stderr else stdout
            if details:
                tail = "\n".join(details.splitlines()[-25:])
                msg += "\n---\nQuarto/LaTeX details (tail):\n" + tail + "\n"

            raise PrereqError(msg)

    _PDF_PREFLIGHT_OK = True


def _run_version_cmd(cmd: list[str]) -> Optional[str]:
    """
    Run a version command and return the first non-empty line from stdout/stderr.

    Returns None if the command cannot be executed or yields no output.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception:
        return None

    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()

    text = out if out else err
    if not text:
        return None

    lines = text.splitlines()
    return lines[0].strip() if lines else None


def get_quarto_version() -> Optional[str]:
    """Return Quarto version string if available (first line), else None."""
    if not has_quarto():
        return None
    return _run_version_cmd(["quarto", "--version"])


def get_pandoc_version() -> Optional[str]:
    """
    Return Pandoc version string if available (first line), else None.

    Note: Pandoc may be bundled with Quarto, but not always exposed on PATH.
    """
    return _run_version_cmd(["pandoc", "--version"])


def _temp_write_check() -> Dict[str, Any]:
    """
    Best-effort check that we can write to the system temp directory.
    Facts only; never raises.
    """
    try:
        base = Path(tempfile.gettempdir())
        test_dir = base / "course-engine-preflight"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "write-test.txt"
        test_file.write_text("ok\n", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return {"ok": True, "temp_dir": str(base)}
    except Exception as e:
        return {"ok": False, "temp_dir": tempfile.gettempdir(), "error": str(e)}


def build_preflight_report() -> Dict[str, Any]:
    """
    Machine-readable preflight report (facts only).
    Designed for: course-engine check --json / --format json
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    quarto_path = get_quarto_path()
    quarto_present = bool(quarto_path)
    quarto_version = get_quarto_version() if quarto_present else None

    pandoc_version = get_pandoc_version()
    pandoc_path = get_pandoc_path()
    pandoc_present = bool(pandoc_version or pandoc_path)

    pdf_ready = False
    pdf_error: Optional[str] = None

    if quarto_present:
        try:
            require_pdf_toolchain()
            pdf_ready = True
        except PrereqError as e:
            pdf_ready = False
            pdf_error = str(e)

    fixes: list[str] = []
    if not quarto_present:
        fixes.append("Install Quarto from https://quarto.org/")
    if quarto_present and not pdf_ready:
        fixes.append("quarto install tinytex")
    if quarto_present and not pandoc_present:
        fixes.append(
            "If pandoc is required, install it or ensure Quarto's bundled pandoc is available on PATH."
        )

    return {
        "mode": "check",
        "generated_at_utc": now,
        "python": {
            "version": sys.version.split()[0],
            "platform": platform.system(),
        },
        "env": {
            "cwd": str(Path.cwd()),
            "path_contains_quarto": bool(quarto_path),
            "path_contains_pandoc": bool(pandoc_path),
        },
        "tools": {
            "quarto": {"present": quarto_present, "version": quarto_version, "path": quarto_path},
            "pandoc": {"present": pandoc_present, "version": pandoc_version, "path": pandoc_path},
        },
        "pdf": {
            "ready": pdf_ready,
            "error": pdf_error,
        },
        "filesystem": {
            "temp_write": _temp_write_check(),
        },
        "fixes": fixes,
    }
