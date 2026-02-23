"""PR subcommands for hatchkit — wraps gh CLI and GraphQL operations."""

from __future__ import annotations

import json

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from hatchkit import gh

pr_app = typer.Typer(
    name="pr",
    help="Interact with GitHub pull request review threads and CI checks.",
    no_args_is_help=True,
)

console = Console()


def _json_out(data: object) -> None:
    """Print data as compact JSON to stdout."""
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@pr_app.command()
def info(
    pretty: bool = typer.Option(False, "--pretty", help="Rich-formatted output for humans."),
) -> None:
    """Show PR number, URL, and branch for the current branch."""
    data = gh.get_pr_info()

    if pretty:
        rprint(f"  PR  : [bold cyan]#{data['number']}[/bold cyan]")
        rprint(f"  URL : [link={data['url']}]{data['url']}[/link]")
        rprint(f"  Branch: {data['headRefName']}")
    else:
        _json_out(data)


@pr_app.command()
def threads(
    owner: str | None = typer.Option(None, "--owner", help="Repository owner (auto-detected)."),
    repo: str | None = typer.Option(None, "--repo", help="Repository name (auto-detected)."),
    pr: int | None = typer.Option(None, "--pr", help="PR number (auto-detected)."),
    all_threads: bool = typer.Option(
        False, "--all", help="Include resolved threads (default: unresolved only)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Rich-formatted output for humans."),
) -> None:
    """Fetch review threads for a pull request."""
    if owner is None or repo is None:
        detected_owner, detected_repo = gh.get_repo_info()
        owner = owner or detected_owner
        repo = repo or detected_repo

    if pr is None:
        pr_info = gh.get_pr_info()
        pr = pr_info["number"]

    thread_list = gh.fetch_review_threads(owner, repo, pr, all_threads=all_threads)

    if pretty:
        if not thread_list:
            rprint("[green]No unresolved threads.[/green]")
            return

        table = Table(title="Review Threads", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", no_wrap=True)
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right")
        table.add_column("Status")
        table.add_column("Comment", max_width=60)

        for i, t in enumerate(thread_list, 1):
            status = "[green]Resolved[/green]" if t["isResolved"] else "[yellow]Open[/yellow]"
            first_comment = ""
            if t.get("comments", {}).get("nodes"):
                first_comment = t["comments"]["nodes"][0].get("body", "")[:60]
            table.add_row(
                str(i),
                t.get("path") or "–",
                str(t.get("line") or "–"),
                status,
                first_comment,
            )

        console.print(table)
        rprint("\n  [dim]Thread IDs (for resolve/reply):[/dim]")
        for i, t in enumerate(thread_list, 1):
            rprint(f"    {i}. {t['id']}")
    else:
        _json_out(thread_list)


@pr_app.command()
def resolve(
    thread_id: str = typer.Argument(help="The node ID of the review thread to resolve."),
    pretty: bool = typer.Option(False, "--pretty", help="Rich-formatted output for humans."),
) -> None:
    """Resolve a review thread."""
    result = gh.resolve_thread(thread_id)

    if pretty:
        rprint(f"[green]Resolved thread[/green] {thread_id}")
    else:
        _json_out(result)


@pr_app.command()
def reply(
    thread_id: str = typer.Argument(help="The node ID of the review thread to reply to."),
    body: str = typer.Argument(help="The reply message body."),
    resolve_thread: bool = typer.Option(
        False, "--resolve", help="Also resolve the thread after replying."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Rich-formatted output for humans."),
) -> None:
    """Reply to a review thread, optionally resolving it."""
    reply_result = gh.reply_to_thread(thread_id, body)

    resolve_result = None
    if resolve_thread:
        resolve_result = gh.resolve_thread(thread_id)

    if pretty:
        rprint(f"[green]Replied to thread[/green] {thread_id}")
        if resolve_thread:
            rprint(f"[green]Resolved thread[/green] {thread_id}")
    else:
        output = {"reply": reply_result}
        if resolve_result is not None:
            output["resolve"] = resolve_result
        _json_out(output)


@pr_app.command()
def checks(
    pretty: bool = typer.Option(False, "--pretty", help="Rich-formatted output for humans."),
) -> None:
    """Show CI check statuses for the current PR."""
    check_list = gh.get_pr_checks()

    if pretty:
        if not check_list:
            rprint("[dim]No checks found.[/dim]")
            return

        table = Table(title="PR Checks", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("State")
        table.add_column("Conclusion")
        table.add_column("Link", style="dim")

        for c in check_list:
            state = c.get("state", "")
            conclusion = c.get("conclusion", "") or "–"
            if conclusion.upper() == "SUCCESS":
                conclusion = f"[green]{conclusion}[/green]"
            elif conclusion.upper() == "FAILURE":
                conclusion = f"[red]{conclusion}[/red]"
            table.add_row(
                c.get("name", "–"),
                state,
                conclusion,
                c.get("link", "") or "–",
            )

        console.print(table)
    else:
        _json_out(check_list)
