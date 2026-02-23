"""GitHub CLI subprocess wrappers and GraphQL helpers."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import typer
from rich import print as rprint


class GhError(Exception):
    """Raised when a gh CLI command fails."""


def require_gh() -> None:
    """Verify that the ``gh`` CLI is installed and on PATH."""
    if shutil.which("gh") is None:
        rprint("[red]Error:[/red] 'gh' CLI not found. Install it from https://cli.github.com/")
        raise typer.Exit(1)


def get_repo_info() -> tuple[str, str]:
    """Return (owner, repo) parsed from the git remote origin URL.

    Supports both HTTPS and SSH remote formats.
    """
    result = _run_command(["git", "remote", "get-url", "origin"])
    url = result.strip()

    # SSH: git@github.com:owner/repo.git
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)

    # HTTPS: https://github.com/owner/repo.git
    m = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)

    rprint(f"[red]Error:[/red] Could not parse owner/repo from remote URL: {url}")
    raise typer.Exit(1)


def get_pr_info() -> dict:
    """Return PR info (number, url, headRefName) for the current branch."""
    result = _run_gh(["pr", "view", "--json", "number,url,headRefName"])
    return json.loads(result)


def fetch_review_threads(
    owner: str, repo: str, pr: int, *, all_threads: bool = False
) -> list[dict]:
    """Fetch review threads for a PR via GraphQL.

    By default returns only unresolved threads. Pass *all_threads=True*
    to include resolved threads as well.
    """
    query = """
    query($owner: String!, $repo: String!, $pr: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr) {
          reviewThreads(first: 100) {
            nodes {
              id
              isResolved
              path
              line
              comments(first: 10) {
                nodes {
                  author { login }
                  body
                  createdAt
                }
              }
            }
          }
        }
      }
    }"""
    variables = {"owner": owner, "repo": repo, "pr": pr}
    data = _run_graphql(query, variables)

    threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]

    if not all_threads:
        threads = [t for t in threads if not t["isResolved"]]

    return threads


def resolve_thread(thread_id: str) -> dict:
    """Resolve a review thread via GraphQL mutation."""
    query = """
    mutation($threadId: ID!) {
      resolveReviewThread(input: { threadId: $threadId }) {
        thread { id isResolved }
      }
    }"""
    variables = {"threadId": thread_id}
    return _run_graphql(query, variables)


def reply_to_thread(thread_id: str, body: str) -> dict:
    """Reply to a review thread via GraphQL mutation."""
    query = """
    mutation($threadId: ID!, $body: String!) {
      addPullRequestReviewThreadReply(input: {
        pullRequestReviewThreadId: $threadId
        body: $body
      }) {
        comment { id body }
      }
    }"""
    variables = {"threadId": thread_id, "body": body}
    return _run_graphql(query, variables)


def get_pr_checks() -> list[dict]:
    """Return CI check statuses for the current PR."""
    result = _run_gh(["pr", "checks", "--json", "name,state,conclusion,link"])
    return json.loads(result)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_command(args: list[str]) -> str:
    """Run a generic command and return stdout."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        rprint(f"[red]Error:[/red] Command not found: {args[0]}")
        raise typer.Exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise GhError(stderr or f"Command failed with exit code {result.returncode}")

    return result.stdout


def _run_gh(args: list[str]) -> str:
    """Run a ``gh`` subcommand and return stdout."""
    require_gh()
    return _run_command(["gh", *args])


def _run_graphql(query: str, variables: dict) -> dict:
    """Run a GraphQL query via ``gh api graphql`` and return parsed JSON.

    Uses ``-f`` for string variables and ``-F`` for integer variables.
    """
    require_gh()

    cmd: list[str] = ["gh", "api", "graphql", "-f", f"query={query}"]

    for key, value in variables.items():
        if isinstance(value, int):
            cmd.extend(["-F", f"{key}={value}"])
        else:
            cmd.extend(["-f", f"{key}={value}"])

    result = _run_command(cmd)
    data = json.loads(result)

    if "errors" in data:
        msgs = [e.get("message", str(e)) for e in data["errors"]]
        rprint(f"[red]GraphQL error:[/red] {'; '.join(msgs)}")
        raise typer.Exit(1)

    return data
