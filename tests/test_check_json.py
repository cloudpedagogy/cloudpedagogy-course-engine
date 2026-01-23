from __future__ import annotations

import json

from typer.testing import CliRunner

from course_engine.cli import app

runner = CliRunner()


def test_check_json_outputs_valid_payload() -> None:
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code in (0, 1, 2)

    payload = json.loads(result.stdout)

    assert payload["mode"] == "check"
    assert "generated_at_utc" in payload

    tools = payload["tools"]
    assert "quarto" in tools
    assert isinstance(tools["quarto"]["present"], bool)

    pdf = payload["pdf"]
    assert isinstance(pdf["ready"], bool)
