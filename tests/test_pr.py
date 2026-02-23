"""Integration tests for the hatchkit pr subcommands."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from hatchkit.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PR_INFO = {"number": 7, "url": "https://github.com/a/b/pull/7", "headRefName": "feat/x"}

_THREADS = [
    {
        "id": "T_abc",
        "isResolved": False,
        "path": "src/main.py",
        "line": 42,
        "comments": {
            "nodes": [{
                "author": {"login": "alice"},
                "body": "Please fix this.",
                "createdAt": "2025-01-01",
            }]
        },
    },
    {
        "id": "T_def",
        "isResolved": True,
        "path": "src/utils.py",
        "line": 10,
        "comments": {
            "nodes": [
                {"author": {"login": "bob"}, "body": "Looks good now.", "createdAt": "2025-01-02"}
            ]
        },
    },
]


# ---------------------------------------------------------------------------
# pr info
# ---------------------------------------------------------------------------


def test_pr_info_json():
    with patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO):
        result = runner.invoke(app, ["pr", "info"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["number"] == 7


def test_pr_info_pretty():
    with patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO):
        result = runner.invoke(app, ["pr", "info", "--pretty"])
    assert result.exit_code == 0
    assert "#7" in result.output
    assert "feat/x" in result.output


# ---------------------------------------------------------------------------
# pr threads
# ---------------------------------------------------------------------------


def test_pr_threads_json_unresolved_only():
    unresolved = [t for t in _THREADS if not t["isResolved"]]
    with (
        patch("hatchkit.gh.get_repo_info", return_value=("a", "b")),
        patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO),
        patch("hatchkit.gh.fetch_review_threads", return_value=unresolved),
    ):
        result = runner.invoke(app, ["pr", "threads"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "T_abc"


def test_pr_threads_json_all():
    with (
        patch("hatchkit.gh.get_repo_info", return_value=("a", "b")),
        patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO),
        patch("hatchkit.gh.fetch_review_threads", return_value=_THREADS),
    ):
        result = runner.invoke(app, ["pr", "threads", "--all"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_pr_threads_explicit_owner_repo_pr():
    unresolved = [t for t in _THREADS if not t["isResolved"]]
    with patch("hatchkit.gh.fetch_review_threads", return_value=unresolved):
        result = runner.invoke(
            app, ["pr", "threads", "--owner", "x", "--repo", "y", "--pr", "99"]
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_pr_threads_pretty():
    unresolved = [t for t in _THREADS if not t["isResolved"]]
    with (
        patch("hatchkit.gh.get_repo_info", return_value=("a", "b")),
        patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO),
        patch("hatchkit.gh.fetch_review_threads", return_value=unresolved),
    ):
        result = runner.invoke(app, ["pr", "threads", "--pretty"])
    assert result.exit_code == 0
    assert "Review Threads" in result.output
    assert "T_abc" in result.output


def test_pr_threads_pretty_no_threads():
    with (
        patch("hatchkit.gh.get_repo_info", return_value=("a", "b")),
        patch("hatchkit.gh.get_pr_info", return_value=_PR_INFO),
        patch("hatchkit.gh.fetch_review_threads", return_value=[]),
    ):
        result = runner.invoke(app, ["pr", "threads", "--pretty"])
    assert result.exit_code == 0
    assert "No unresolved threads" in result.output


# ---------------------------------------------------------------------------
# pr resolve
# ---------------------------------------------------------------------------


def test_pr_resolve_json():
    resolve_resp = {
        "data": {"resolveReviewThread": {"thread": {"id": "T_abc", "isResolved": True}}}
    }
    with patch("hatchkit.gh.resolve_thread", return_value=resolve_resp):
        result = runner.invoke(app, ["pr", "resolve", "T_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["resolveReviewThread"]["thread"]["isResolved"] is True


def test_pr_resolve_pretty():
    resolve_resp = {
        "data": {"resolveReviewThread": {"thread": {"id": "T_abc", "isResolved": True}}}
    }
    with patch("hatchkit.gh.resolve_thread", return_value=resolve_resp):
        result = runner.invoke(app, ["pr", "resolve", "T_abc", "--pretty"])
    assert result.exit_code == 0
    assert "Resolved thread" in result.output


# ---------------------------------------------------------------------------
# pr reply
# ---------------------------------------------------------------------------


def test_pr_reply_json():
    reply_resp = {
        "data": {"addPullRequestReviewThreadReply": {"comment": {"id": "c1", "body": "Fixed!"}}}
    }
    with patch("hatchkit.gh.reply_to_thread", return_value=reply_resp):
        result = runner.invoke(app, ["pr", "reply", "T_abc", "Fixed!"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "reply" in data


def test_pr_reply_with_resolve():
    reply_resp = {
        "data": {"addPullRequestReviewThreadReply": {"comment": {"id": "c1", "body": "Fixed!"}}}
    }
    resolve_resp = {
        "data": {"resolveReviewThread": {"thread": {"id": "T_abc", "isResolved": True}}}
    }
    with (
        patch("hatchkit.gh.reply_to_thread", return_value=reply_resp),
        patch("hatchkit.gh.resolve_thread", return_value=resolve_resp),
    ):
        result = runner.invoke(app, ["pr", "reply", "T_abc", "Fixed!", "--resolve"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "reply" in data
    assert "resolve" in data


def test_pr_reply_pretty():
    reply_resp = {
        "data": {"addPullRequestReviewThreadReply": {"comment": {"id": "c1", "body": "Fixed!"}}}
    }
    with patch("hatchkit.gh.reply_to_thread", return_value=reply_resp):
        result = runner.invoke(app, ["pr", "reply", "T_abc", "Fixed!", "--pretty"])
    assert result.exit_code == 0
    assert "Replied to thread" in result.output


def test_pr_reply_pretty_with_resolve():
    reply_resp = {
        "data": {"addPullRequestReviewThreadReply": {"comment": {"id": "c1", "body": "Fixed!"}}}
    }
    resolve_resp = {
        "data": {"resolveReviewThread": {"thread": {"id": "T_abc", "isResolved": True}}}
    }
    with (
        patch("hatchkit.gh.reply_to_thread", return_value=reply_resp),
        patch("hatchkit.gh.resolve_thread", return_value=resolve_resp),
    ):
        result = runner.invoke(app, ["pr", "reply", "T_abc", "Fixed!", "--resolve", "--pretty"])
    assert result.exit_code == 0
    assert "Replied to thread" in result.output
    assert "Resolved thread" in result.output


# ---------------------------------------------------------------------------
# pr checks
# ---------------------------------------------------------------------------


def test_pr_checks_json():
    checks_data = [
        {"name": "ci", "state": "completed", "conclusion": "success", "link": "https://ci.example.com/1"}
    ]
    with patch("hatchkit.gh.get_pr_checks", return_value=checks_data):
        result = runner.invoke(app, ["pr", "checks"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["name"] == "ci"


def test_pr_checks_pretty():
    checks_data = [
        {"name": "ci", "state": "completed", "conclusion": "SUCCESS", "link": "https://ci.example.com/1"}
    ]
    with patch("hatchkit.gh.get_pr_checks", return_value=checks_data):
        result = runner.invoke(app, ["pr", "checks", "--pretty"])
    assert result.exit_code == 0
    assert "PR Checks" in result.output
    assert "ci" in result.output


def test_pr_checks_pretty_no_checks():
    with patch("hatchkit.gh.get_pr_checks", return_value=[]):
        result = runner.invoke(app, ["pr", "checks", "--pretty"])
    assert result.exit_code == 0
    assert "No checks found" in result.output


# ---------------------------------------------------------------------------
# pr --help
# ---------------------------------------------------------------------------


def test_pr_help():
    result = runner.invoke(app, ["pr", "--help"])
    assert result.exit_code == 0
    assert "threads" in result.output
    assert "resolve" in result.output
    assert "reply" in result.output
    assert "checks" in result.output
    assert "info" in result.output
