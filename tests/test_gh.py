"""Unit tests for hatchkit.gh — GitHub CLI wrappers."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest
import typer

from hatchkit import gh

# ---------------------------------------------------------------------------
# require_gh
# ---------------------------------------------------------------------------


def test_require_gh_found():
    with patch("shutil.which", return_value="/usr/bin/gh"):
        gh.require_gh()  # should not raise


def test_require_gh_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(typer.Exit):
            gh.require_gh()


# ---------------------------------------------------------------------------
# get_repo_info
# ---------------------------------------------------------------------------


def test_get_repo_info_https():
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="https://github.com/alice/my-repo.git\n", stderr=""
    )
    with patch("subprocess.run", return_value=fake):
        owner, repo = gh.get_repo_info()
    assert owner == "alice"
    assert repo == "my-repo"


def test_get_repo_info_https_no_dotgit():
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="https://github.com/alice/my-repo\n", stderr=""
    )
    with patch("subprocess.run", return_value=fake):
        owner, repo = gh.get_repo_info()
    assert owner == "alice"
    assert repo == "my-repo"


def test_get_repo_info_ssh():
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="git@github.com:bob/cool-project.git\n", stderr=""
    )
    with patch("subprocess.run", return_value=fake):
        owner, repo = gh.get_repo_info()
    assert owner == "bob"
    assert repo == "cool-project"


def test_get_repo_info_ssh_no_dotgit():
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="git@github.com:bob/cool-project\n", stderr=""
    )
    with patch("subprocess.run", return_value=fake):
        owner, repo = gh.get_repo_info()
    assert owner == "bob"
    assert repo == "cool-project"


def test_get_repo_info_unparseable():
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="https://gitlab.com/x/y.git\n", stderr=""
    )
    with patch("subprocess.run", return_value=fake):
        with pytest.raises(typer.Exit):
            gh.get_repo_info()


# ---------------------------------------------------------------------------
# get_pr_info
# ---------------------------------------------------------------------------


def test_get_pr_info():
    payload = {"number": 42, "url": "https://github.com/a/b/pull/42", "headRefName": "feat/x"}
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(payload), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.get_pr_info()
    assert result["number"] == 42
    assert result["headRefName"] == "feat/x"


# ---------------------------------------------------------------------------
# fetch_review_threads
# ---------------------------------------------------------------------------


def _make_thread(thread_id: str, *, resolved: bool = False, path: str = "f.py") -> dict:
    return {
        "id": thread_id,
        "isResolved": resolved,
        "path": path,
        "line": 10,
        "comments": {"nodes": [{"author": {"login": "rev"}, "body": "fix", "createdAt": "now"}]},
    }


def test_fetch_review_threads_filters_resolved():
    threads = [_make_thread("t1", resolved=False), _make_thread("t2", resolved=True)]
    graphql_response = {
        "data": {
            "repository": {"pullRequest": {"reviewThreads": {"nodes": threads}}}
        }
    }
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(graphql_response), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.fetch_review_threads("owner", "repo", 1)
    assert len(result) == 1
    assert result[0]["id"] == "t1"


def test_fetch_review_threads_all():
    threads = [_make_thread("t1", resolved=False), _make_thread("t2", resolved=True)]
    graphql_response = {
        "data": {
            "repository": {"pullRequest": {"reviewThreads": {"nodes": threads}}}
        }
    }
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(graphql_response), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.fetch_review_threads("owner", "repo", 1, all_threads=True)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# resolve_thread
# ---------------------------------------------------------------------------


def test_resolve_thread():
    graphql_response = {
        "data": {"resolveReviewThread": {"thread": {"id": "t1", "isResolved": True}}}
    }
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(graphql_response), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.resolve_thread("t1")
    assert result["data"]["resolveReviewThread"]["thread"]["isResolved"] is True


# ---------------------------------------------------------------------------
# reply_to_thread
# ---------------------------------------------------------------------------


def test_reply_to_thread():
    graphql_response = {
        "data": {
            "addPullRequestReviewThreadReply": {"comment": {"id": "c1", "body": "done"}}
        }
    }
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(graphql_response), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.reply_to_thread("t1", "done")
    assert result["data"]["addPullRequestReviewThreadReply"]["comment"]["body"] == "done"


# ---------------------------------------------------------------------------
# get_pr_checks
# ---------------------------------------------------------------------------


def test_get_pr_checks():
    checks = [{"name": "ci", "state": "completed", "conclusion": "success", "link": ""}]
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(checks), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            result = gh.get_pr_checks()
    assert result[0]["name"] == "ci"


# ---------------------------------------------------------------------------
# _run_graphql error handling
# ---------------------------------------------------------------------------


def test_run_graphql_raises_on_errors():
    response = {"errors": [{"message": "Something went wrong"}]}
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(response), stderr=""
    )
    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("subprocess.run", return_value=fake):
            with pytest.raises(typer.Exit):
                gh._run_graphql("query { viewer { login } }", {})


# ---------------------------------------------------------------------------
# _run_command error handling
# ---------------------------------------------------------------------------


def test_run_command_nonzero_exit():
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="fatal: not a git repo"
    )
    with patch("subprocess.run", return_value=fake):
        with pytest.raises(gh.GhError, match="not a git repo"):
            gh._run_command(["git", "status"])


def test_run_command_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(typer.Exit):
            gh._run_command(["nonexistent"])
