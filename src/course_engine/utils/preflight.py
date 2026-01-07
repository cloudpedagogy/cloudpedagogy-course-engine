from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class PrereqError(RuntimeError):
    """Raised when an external prerequisite is missing."""


# Cache PDF preflight result per process to avoid re-checking repeatedly.
_PDF_PREFLIGHT_OK: Optional[bool] = None


def has_quarto() -> bool:
    """Return True if Quarto is available on PATH."""
    return shutil.which("quarto") is not None


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

        # Minimal config forcing PDF format (engine left default)
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
