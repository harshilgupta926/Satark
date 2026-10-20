from __future__ import annotations

from io import StringIO
import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import scripts.firstlight_live_response as cli


class TTYInput(StringIO):
    def isatty(self):
        return True


def test_live_response_requires_second_opt_in(capsys):
    assert cli.main(["--action", "isolate-device", "--target", "device-1", "--reason", "case FL-1"]) == 2
    assert "No action performed" in capsys.readouterr().err


def test_live_response_refuses_noninteractive_execution(monkeypatch, capsys):
    monkeypatch.setattr(cli, "live_response_enabled", lambda: True)
    monkeypatch.setattr(sys, "stdin", StringIO("CONFIRM ISOLATE device-1\n"))
    assert cli.main([
        "--action", "isolate-device", "--target", "device-1", "--reason", "case FL-1", "--execute-live-action"
    ]) == 2
    assert "interactive terminal" in capsys.readouterr().err


def test_wrong_confirmation_never_calls_provider(monkeypatch, capsys):
    monkeypatch.setattr(cli, "live_response_enabled", lambda: True)
    monkeypatch.setattr(sys, "stdin", TTYInput("yes\n"))
    with patch.object(cli, "isolate_defender_device") as action:
        assert cli.main([
            "--action", "isolate-device", "--target", "device-1", "--reason", "case FL-1", "--execute-live-action"
        ]) == 2
        action.assert_not_called()
    assert "confirmation did not match" in capsys.readouterr().err


def test_exact_confirmation_calls_only_explicit_target(monkeypatch, capsys):
    monkeypatch.setattr(cli, "live_response_enabled", lambda: True)
    monkeypatch.setattr(sys, "stdin", TTYInput("CONFIRM REVOKE_SESSIONS analyst@example.com\n"))
    expected = SimpleNamespace(
        provider="Microsoft Entra ID",
        action="revoke_sign_in_sessions",
        target="analyst@example.com",
        status="submitted",
        detail="Provider accepted the request",
    )
    with patch.object(cli, "revoke_entra_user_sessions", return_value=expected) as action:
        code = cli.main([
            "--action", "revoke-user-sessions", "--target", "analyst@example.com",
            "--reason", "case FL-1", "--execute-live-action"
        ])
    assert code == 0
    action.assert_called_once_with(
        "analyst@example.com",
        confirmation="CONFIRM REVOKE_SESSIONS analyst@example.com",
        reason="case FL-1",
    )
    captured = capsys.readouterr().out
    output = json.loads(captured[captured.index("{"):])
    assert output["status"] == "submitted"
    assert "not proof of completion" in output["note"]
