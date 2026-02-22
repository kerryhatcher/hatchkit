"""hatchkit CLI – A tool to help with AI driven development."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hatchkit import __version__

app = typer.Typer(
    name="hatchkit",
    help="A tool to help with AI driven development.",
    add_completion=True,
    no_args_is_help=True,
)

console = Console()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TOOLS_TO_CHECK: dict[str, str] = {
    "git": "Version control – required for most workflows",
    "uv": "Python package/environment manager",
    "claude": "Anthropic Claude Code agent",
    "gemini": "Google Gemini CLI agent",
    "code": "Visual Studio Code",
    "cursor": "Cursor AI editor",
    "codex": "OpenAI Codex CLI",
}


def _tool_status(name: str) -> tuple[bool, str]:
    """Return (found, version_or_path) for a CLI tool."""
    path = shutil.which(name)
    if path is None:
        return False, ""
    try:
        result = subprocess.run(
            [name, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = (result.stdout or result.stderr).strip().splitlines()[0]
    except Exception:
        version = path
    return True, version


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show the hatchkit version."""
    rprint(f"hatchkit [bold cyan]{__version__}[/bold cyan]")


@app.command()
def check() -> None:
    """Check for required tools and AI agents on your system."""
    table = Table(title="Tool Check", show_header=True, header_style="bold magenta")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Details")
    table.add_column("Description", style="dim")

    all_found = True
    for tool, description in TOOLS_TO_CHECK.items():
        found, details = _tool_status(tool)
        if found:
            status = "[green]✔ found[/green]"
        else:
            status = "[red]✘ missing[/red]"
            all_found = False
        table.add_row(tool, status, details or "–", description)

    console.print(table)

    if all_found:
        rprint("\n[green]All tools found![/green]")
    else:
        rprint(
            "\n[yellow]Some tools are missing."
            " Install them to unlock full functionality.[/yellow]"
        )


@app.command()
def init(
    project_name: str | None = typer.Argument(
        None,
        help="Name of the new project directory. Omit to initialise in the current directory.",
    ),
    here: bool = typer.Option(
        False,
        "--here",
        help="Initialise in the current directory instead of creating a new one.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files without prompting.",
    ),
    ai: str | None = typer.Option(
        None,
        "--ai",
        help="AI agent to configure: claude, copilot, cursor, gemini, codex, or generic.",
    ),
) -> None:
    """Initialise a new hatchkit project with AI agent configuration."""
    # Resolve target directory
    if here or project_name in (None, "."):
        target = Path.cwd()
        created_dir = False
    else:
        target = Path.cwd() / project_name
        created_dir = not target.exists()

    if created_dir:
        target.mkdir(parents=True, exist_ok=True)
        rprint(f"[green]Created directory[/green] [bold]{target}[/bold]")
    else:
        rprint(f"[cyan]Using existing directory[/cyan] [bold]{target}[/bold]")

    # Validate AI option
    supported_agents = {"claude", "copilot", "cursor", "gemini", "codex", "generic"}
    if ai and ai not in supported_agents:
        rprint(
            f"[red]Unknown AI agent:[/red] '{ai}'. "
            f"Supported: {', '.join(sorted(supported_agents))}"
        )
        raise typer.Exit(1)

    _write_project_files(target, ai=ai, force=force)

    rprint(
        Panel.fit(
            f"[bold green]✔ hatchkit project initialised[/bold green]\n\n"
            f"  Directory : [cyan]{target}[/cyan]\n"
            f"  AI agent  : [cyan]{ai or 'none'}[/cyan]\n\n"
            "Next steps:\n"
            "  1. Open the project in your AI editor\n"
            "  2. Review [bold].hatchkit/AGENTS.md[/bold] and customise as needed\n"
            "  3. Start building with AI-driven development!",
            title="hatchkit init",
            border_style="green",
        )
    )


# ---------------------------------------------------------------------------
# Project scaffolding helpers
# ---------------------------------------------------------------------------

_AGENTS_MD_TEMPLATE = """\
# hatchkit – AI Agent Guidelines

This project uses **hatchkit** for AI-driven development.

## Development Principles

- Write clear, self-documenting code
- Prefer small, focused functions and modules
- Always add or update tests when changing behaviour
- Keep dependencies minimal

## Workflow

1. Discuss the requirement and agree on an approach
2. Implement the smallest change that satisfies the requirement
3. Verify with tests and linting before marking work complete
"""

_GITIGNORE_ADDITIONS = """\
# hatchkit
.hatchkit/cache/
"""


def _write_project_files(target: Path, ai: str | None, force: bool) -> None:
    """Write the hatchkit scaffold files into *target*."""
    hatchkit_dir = target / ".hatchkit"
    hatchkit_dir.mkdir(exist_ok=True)

    _write_file(hatchkit_dir / "AGENTS.md", _AGENTS_MD_TEMPLATE, force=force)

    if ai:
        _write_ai_config(target, ai, force=force)

    # Append to .gitignore if present
    gitignore = target / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if "# hatchkit" not in content:
            gitignore.write_text(content + "\n" + _GITIGNORE_ADDITIONS)
            rprint("  [dim]Updated .gitignore[/dim]")


def _write_ai_config(target: Path, ai: str, force: bool) -> None:
    """Write AI-agent-specific command files."""
    if ai == "claude":
        commands_dir = target / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        _write_file(commands_dir / "hatchkit.md", _agent_command_md("Claude Code"), force=force)
        rprint("  [dim]Wrote Claude Code commands → .claude/commands/hatchkit.md[/dim]")

    elif ai == "copilot":
        instructions_dir = target / ".github"
        instructions_dir.mkdir(parents=True, exist_ok=True)
        _write_file(
            instructions_dir / "copilot-instructions.md",
            _copilot_instructions_md(),
            force=force,
        )
        rprint("  [dim]Wrote Copilot instructions → .github/copilot-instructions.md[/dim]")

    elif ai == "cursor":
        rules_dir = target / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        _write_file(rules_dir / "hatchkit.mdc", _agent_command_md("Cursor"), force=force)
        rprint("  [dim]Wrote Cursor rules → .cursor/rules/hatchkit.mdc[/dim]")

    elif ai == "gemini":
        commands_dir = target / ".gemini"
        commands_dir.mkdir(parents=True, exist_ok=True)
        _write_file(commands_dir / "GEMINI.md", _agent_command_md("Gemini CLI"), force=force)
        rprint("  [dim]Wrote Gemini CLI config → .gemini/GEMINI.md[/dim]")

    elif ai in ("codex", "generic"):
        commands_dir = target / ".ai" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        _write_file(commands_dir / "hatchkit.md", _agent_command_md(ai.title()), force=force)
        rprint(f"  [dim]Wrote {ai.title()} commands → .ai/commands/hatchkit.md[/dim]")


def _write_file(path: Path, content: str, force: bool) -> None:
    """Write *content* to *path*, respecting the *force* flag."""
    if path.exists() and not force:
        rprint(f"  [yellow]Skipped (already exists):[/yellow] {path.relative_to(path.parents[2])}")
        return
    path.write_text(content)
    try:
        rel = path.relative_to(Path.cwd())
    except ValueError:
        rel = path
    rprint(f"  [green]Wrote:[/green] {rel}")


def _agent_command_md(agent_name: str) -> str:
    return f"""\
# hatchkit AI Development Guidelines

These guidelines apply to all {agent_name} interactions in this project.

## Principles

- Make the **smallest** change that satisfies the requirement
- Always run existing tests before and after changes
- Prefer clear, readable code over clever optimisations
- Document non-obvious decisions with brief comments

## Workflow

1. Understand the requirement fully before writing any code
2. Identify the minimal set of files to change
3. Write or update tests first when adding new behaviour
4. Verify with linting and tests
5. Summarise what changed and why
"""


def _copilot_instructions_md() -> str:
    return """\
# GitHub Copilot Instructions

This project uses **hatchkit** for AI-driven development.

## Coding Style

- Python 3.10+ syntax; use `match`/`case` where it improves clarity
- Type-annotate all public functions
- Keep functions small and focused (≤ 30 lines where possible)
- Use `rich` for all console output

## Testing

- All new behaviour must be covered by a `pytest` test
- Run `uv run pytest` to execute the test suite
- Run `uv run ruff check .` to lint before committing
"""


def main() -> None:
    """Entry point used by the `hatchkit` console script."""
    app()


if __name__ == "__main__":
    main()
