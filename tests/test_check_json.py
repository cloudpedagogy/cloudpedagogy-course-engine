from __future__ import annotations

import json

from typer.testing import CliRunner

from course_engine.cli import app

runner = CliRunner()


def _assert_check_payload(payload: dict) -> None:
    assert payload["mode"] == "check"
    assert "generated_at_utc" in payload

    # Core blocks
    assert "python" in payload
    assert "tools" in payload
    assert "pdf" in payload

    tools = payload["tools"]
    assert "quarto" in tools
    assert isinstance(tools["quarto"]["present"], bool)

    pdf = payload["pdf"]
    assert isinstance(pdf["ready"], bool)

    # Optional / adoption-grade additions (should not break if missing)
    # If present, they should be sane.
    if "path" in tools.get("quarto", {}):
        assert (tools["quarto"]["path"] is None) or isinstance(tools["quarto"]["path"], str)
    if "path" in tools.get("pandoc", {}):
        assert (tools["pandoc"]["path"] is None) or isinstance(tools["pandoc"]["path"], str)


def test_check_format_json_outputs_valid_payload() -> None:
    result = runner.invoke(app, ["check", "--format", "json"])
    assert result.exit_code in (0, 1, 2)

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)


def test_check_legacy_json_flag_outputs_valid_payload() -> None:
    # Back-compat: --json should still work and produce JSON
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code in (0, 1, 2)

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)
