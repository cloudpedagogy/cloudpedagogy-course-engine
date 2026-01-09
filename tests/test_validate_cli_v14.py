from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()


def test_validate_list_profiles_exits_zero_without_manifest(tmp_path: Path):
    # No manifest.json in tmp_path — this must still work in list-only mode.
    from course_engine.cli import app

    result = runner.invoke(
        app,
        [
            "validate",
            str(tmp_path),
            "--policy",
            "preset:baseline",
            "--list-profiles",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "baseline" in result.output.lower()


def test_validate_explain_exits_zero_without_manifest(tmp_path: Path):
    # No manifest.json in tmp_path — explain-only should still work.
    from course_engine.cli import app

    result = runner.invoke(
        app,
        [
            "validate",
            str(tmp_path),
            "--policy",
            "preset:baseline",
            "--profile",
            "baseline",
            "--explain",
        ],
    )

    assert result.exit_code == 0, result.output
    # should print policy/profile context
    out = result.output.lower()
    assert "policy" in out
    assert "profile" in out
