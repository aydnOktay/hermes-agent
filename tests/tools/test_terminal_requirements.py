import logging
from pathlib import Path

import pytest

from tools.terminal_tool import check_terminal_requirements


def _clear_terminal_env(monkeypatch):
    """Helper to remove TERMINAL_* env vars that could affect tests."""
    keys = [
        "TERMINAL_ENV",
        "TERMINAL_SSH_HOST",
        "TERMINAL_SSH_USER",
        "MODAL_TOKEN_ID",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_unknown_terminal_env_logs_error_and_returns_false(monkeypatch, caplog):
    """Unknown TERMINAL_ENV should log a clear error and return False."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "unknown-backend")

    with caplog.at_level(logging.ERROR):
        ok = check_terminal_requirements()

    assert ok is False
    assert any(
        "Unknown TERMINAL_ENV 'unknown-backend'" in record.getMessage()
        for record in caplog.records
    )


def test_ssh_backend_without_host_or_user_logs_and_returns_false(monkeypatch, caplog):
    """SSH backend requires both TERMINAL_SSH_HOST and TERMINAL_SSH_USER."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "ssh")
    # Leave TERMINAL_SSH_HOST / TERMINAL_SSH_USER unset on purpose

    with caplog.at_level(logging.ERROR):
        ok = check_terminal_requirements()

    assert ok is False
    assert any(
        "SSH backend selected but TERMINAL_SSH_HOST and TERMINAL_SSH_USER" in record.getMessage()
        for record in caplog.records
    )


def test_modal_backend_without_token_logs_and_returns_false(monkeypatch, caplog, tmp_path):
    """Modal backend should surface a clear error when no token/config is present."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "modal")

    # Ensure MODAL_TOKEN_ID is not set and ~/.modal.toml doesn't exist
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)

    # Point HOME to a temp directory so Path.home()/.modal.toml is absent
    monkeypatch.setenv("HOME", str(tmp_path))
    # On Windows, also set USERPROFILE which Path.home() may consult
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    with caplog.at_level(logging.ERROR):
        ok = check_terminal_requirements()

    assert ok is False
    messages = [record.getMessage() for record in caplog.records]
    # In environments without minisweagent installed, we at least expect a generic
    # terminal requirements failure. When minisweagent is available, the more
    # specific Modal configuration error should be logged.
    assert any(
        "Modal backend selected but no MODAL_TOKEN_ID environment variable" in m
        for m in messages
    ) or any("Terminal requirements check failed" in m for m in messages)

