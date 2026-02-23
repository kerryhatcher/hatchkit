"""Tests for the hatchkit CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from hatchkit import __version__
from hatchkit.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def test_check_command_runs():
    """check should always exit 0 regardless of which tools are installed."""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    # Table headers should be present
    assert "Tool Check" in result.output or "tool" in result.output.lower()


# ---------------------------------------------------------------------------
# init – basic usage
# ---------------------------------------------------------------------------


def test_init_creates_directory(tmp_path):
    result = runner.invoke(app, ["init", "my-project"], catch_exceptions=False)
    # The runner uses CWD, so we check stdout for the project name
    assert result.exit_code == 0
    assert "my-project" in result.output


def test_init_here_creates_hatchkit_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".hatchkit" / "AGENTS.md").exists()


def test_init_dot_creates_hatchkit_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "."], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".hatchkit" / "AGENTS.md").exists()


def test_init_with_claude_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "claude"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "commands" / "hatchkit.md").exists()
    assert (tmp_path / ".claude" / "commands" / "hatchkit.prfix.md").exists()


def test_init_claude_creates_prfix_command(tmp_path, monkeypatch):
    """The prfix template should contain key markers like the frontmatter and GraphQL reference."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--here", "--ai", "claude"], catch_exceptions=False)
    prfix = (tmp_path / ".claude" / "commands" / "hatchkit.prfix.md").read_text()
    assert "description: Review and resolve all unresolved review threads" in prfix
    assert "resolveReviewThread" in prfix
    assert "GraphQL Quick Reference" in prfix


def test_init_with_copilot_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "copilot"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()


def test_init_with_cursor_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "cursor"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".cursor" / "rules" / "hatchkit.mdc").exists()


def test_init_with_gemini_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "gemini"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".gemini" / "GEMINI.md").exists()


def test_init_with_generic_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "generic"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".ai" / "commands" / "hatchkit.md").exists()


def test_init_invalid_ai_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--here", "--ai", "notanagent"])
    assert result.exit_code != 0


def test_init_skips_existing_file_without_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # First init
    runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    agents_md = tmp_path / ".hatchkit" / "AGENTS.md"

    # Modify the file manually
    agents_md.write_text("custom content")

    # Second init without --force should NOT overwrite
    runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    assert agents_md.read_text() == "custom content"


def test_init_force_overwrites_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    agents_md = tmp_path / ".hatchkit" / "AGENTS.md"
    agents_md.write_text("custom content")

    # With --force it should overwrite
    runner.invoke(app, ["init", "--here", "--force"], catch_exceptions=False)
    assert agents_md.read_text() != "custom content"


def test_init_updates_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n")

    runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    content = gitignore.read_text()
    assert "# hatchkit" in content


def test_init_does_not_duplicate_gitignore_entry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n")

    runner.invoke(app, ["init", "--here"], catch_exceptions=False)
    runner.invoke(app, ["init", "--here", "--force"], catch_exceptions=False)
    content = gitignore.read_text()
    assert content.count("# hatchkit") == 1
