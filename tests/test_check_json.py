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

    # v1.20+ additive: requirements block (contract for CI/support interpretation)
    assert "requirements" in payload
    req = payload["requirements"]
    assert isinstance(req, dict)

    # Tighten contract: keys should exist (CLI always sets these)
    assert "mode" in req
    assert "require_pdf" in req
    assert "require_quarto" in req

    assert req["mode"] in {"default", "strict"}
    assert isinstance(req["require_pdf"], bool)
    assert isinstance(req["require_quarto"], bool)

    # Optional placeholder if you include it
    if "require_pandoc" in req:
        assert isinstance(req["require_pandoc"], bool)

    # Optional / adoption-grade additions (should not break if missing)
    if "path" in tools.get("quarto", {}):
        assert (tools["quarto"]["path"] is None) or isinstance(tools["quarto"]["path"], str)
    if "path" in tools.get("pandoc", {}):
        assert (tools["pandoc"]["path"] is None) or isinstance(tools["pandoc"]["path"], str)


def test_check_format_json_outputs_valid_payload() -> None:
    # v1.20: default check is informational (does not fail CI by default)
    result = runner.invoke(app, ["check", "--format", "json"])
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)

    # Default requirements (informational mode)
    req = payload["requirements"]
    assert req["mode"] == "default"
    assert req["require_quarto"] is False
    assert req["require_pdf"] is False


def test_check_legacy_json_flag_outputs_valid_payload() -> None:
    # Back-compat: --json should still work and produce JSON
    # v1.20: default mode remains informational
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)

    req = payload["requirements"]
    assert req["mode"] == "default"
    assert req["require_quarto"] is False
    assert req["require_pdf"] is False


def test_check_strict_sets_requirements_and_exit_code_is_deterministic() -> None:
    # v1.20: strict mode is CI-grade and may fail depending on environment readiness.
    result = runner.invoke(app, ["check", "--format", "json", "--strict"])
    assert result.exit_code in (0, 2, 3, 4)

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)

    req = payload["requirements"]
    assert req["mode"] == "strict"
    assert req["require_quarto"] is True
    assert req["require_pdf"] is True


def test_check_require_pdf_sets_requirements_and_exit_code_is_deterministic() -> None:
    # v1.20: requiring pdf should imply Quarto is required (PDF readiness depends on Quarto).
    result = runner.invoke(app, ["check", "--format", "json", "--require", "pdf"])
    assert result.exit_code in (0, 2, 3, 4)

    payload = json.loads(result.stdout)
    _assert_check_payload(payload)

    req = payload["requirements"]
    assert req["mode"] == "default"
    assert req["require_pdf"] is True
    assert req["require_quarto"] is True
