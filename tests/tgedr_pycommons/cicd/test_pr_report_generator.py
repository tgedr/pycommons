"""Unit tests for pr_report_generator module."""
import json
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from tgedr_pycommons.cicd.pr_report_generator import (
    DefaultPrReportGeneratorStrategy,
    GitHubPrReportGenerator,
    PrMerge,
    PrReportData,
    PrReportGeneratorStrategy,
    PrReview,
    generate_pr_approvals_md,
    main,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

REVIEW_DICT = {
    "id": "rev-1",
    "author": {"login": "alice"},
    "submittedAt": "2026-01-01T10:00:00Z",
    "state": "APPROVED",
}

PR_DICT_WITH_REVIEWS = {
    "number": 42,
    "title": "feat: add feature",
    "url": "https://github.com/org/repo/pull/42",
    "mergedAt": "2026-01-02T12:00:00Z",
    "mergeCommit": {"oid": "abc123"},
    "reviews": [REVIEW_DICT],
}

PR_DICT_NO_REVIEWS = {
    "number": 7,
    "title": "fix: bug fix",
    "url": "https://github.com/org/repo/pull/7",
    "mergedAt": "2026-01-03T08:00:00Z",
    "mergeCommit": {"oid": "def456"},
    "reviews": [],
}


# ---------------------------------------------------------------------------
# PrReview
# ---------------------------------------------------------------------------


def test_pr_review_from_dict():
    review = PrReview.from_dict(REVIEW_DICT)
    assert review.id == "rev-1"
    assert review.author == "alice"
    assert review.submitted_at == "2026-01-01T10:00:00Z"
    assert review.state == "APPROVED"


# ---------------------------------------------------------------------------
# PrMerge
# ---------------------------------------------------------------------------


def test_pr_merge_from_dict_with_reviews():
    pr = PrMerge.from_dict(PR_DICT_WITH_REVIEWS)
    assert pr.number == 42
    assert pr.title == "feat: add feature"
    assert pr.url == "https://github.com/org/repo/pull/42"
    assert pr.merged_at == "2026-01-02T12:00:00Z"
    assert pr.merge_commit_id == "abc123"
    assert len(pr.reviews) == 1
    assert pr.reviews[0].author == "alice"


def test_pr_merge_from_dict_no_reviews():
    pr = PrMerge.from_dict(PR_DICT_NO_REVIEWS)
    assert pr.reviews == []


# ---------------------------------------------------------------------------
# PrReportData
# ---------------------------------------------------------------------------


def test_pr_report_data_fields():
    data = PrReportData(repo="org/repo", branch="main", pr_merges=[])
    assert data.repo == "org/repo"
    assert data.branch == "main"
    assert data.pr_merges == []


# ---------------------------------------------------------------------------
# PrReportGeneratorStrategy
# ---------------------------------------------------------------------------


def test_get_instance_returns_default():
    instance = PrReportGeneratorStrategy.get_instance(None)
    assert isinstance(instance, DefaultPrReportGeneratorStrategy)


def test_get_instance_with_name_returns_default():
    instance = PrReportGeneratorStrategy.get_instance("some-strategy")
    assert isinstance(instance, DefaultPrReportGeneratorStrategy)


# ---------------------------------------------------------------------------
# DefaultPrReportGeneratorStrategy
# ---------------------------------------------------------------------------


def test_generate_report_with_reviews():
    strategy = DefaultPrReportGeneratorStrategy()
    pr = PrMerge.from_dict(PR_DICT_WITH_REVIEWS)
    data = PrReportData(repo="org/repo", branch="main", pr_merges=[pr])

    lines = strategy.generate_report(data)

    assert lines[0] == "# PR Approvals for repository: org/repo (branch: main)"
    assert "## PR #42: feat: add feature" in lines
    assert any("https://github.com/org/repo/pull/42" in line for line in lines)
    assert any("abc123" in line for line in lines)
    assert any("Reviews:" in line for line in lines)
    assert any("alice" in line and "APPROVED" in line for line in lines)


def test_generate_report_no_reviews():
    strategy = DefaultPrReportGeneratorStrategy()
    pr = PrMerge.from_dict(PR_DICT_NO_REVIEWS)
    data = PrReportData(repo="org/repo", branch="main", pr_merges=[pr])

    lines = strategy.generate_report(data)

    assert any("No reviews" in line for line in lines)


def test_generate_report_empty_prs():
    strategy = DefaultPrReportGeneratorStrategy()
    data = PrReportData(repo="org/repo", branch="main", pr_merges=[])

    lines = strategy.generate_report(data)

    assert len(lines) == 1
    assert "org/repo" in lines[0]


# ---------------------------------------------------------------------------
# GitHubPrReportGenerator / PrReportGenerator
# ---------------------------------------------------------------------------

REVIEW_DICT_COMMENTED = {
    "id": "rev-2",
    "author": {"login": "bob"},
    "submittedAt": "2026-01-01T11:00:00Z",
    "state": "COMMENTED",
}

PR_DICT_MIXED_REVIEWS = {
    "number": 99,
    "title": "chore: mixed reviews",
    "url": "https://github.com/org/repo/pull/99",
    "mergedAt": "2026-01-04T09:00:00Z",
    "mergeCommit": {"oid": "ghi789"},
    "reviews": [REVIEW_DICT, REVIEW_DICT_COMMENTED],
}


def _make_gh_response(pr_dicts: list) -> CompletedProcess:
    return CompletedProcess(args=[], returncode=0, stdout=json.dumps(pr_dicts), stderr="")


def test_github_generator_get_pr_report_data():
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_WITH_REVIEWS, PR_DICT_NO_REVIEWS])
        generator = GitHubPrReportGenerator("org/repo", "main", max_prs=100)
        data = generator._get_pr_report_data()  # noqa: SLF001

    assert data.repo == "org/repo"
    assert data.branch == "main"
    assert len(data.pr_merges) == 2
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "gh" in call_args
    assert "--limit" in call_args
    assert "100" in call_args


def test_github_generator_get_pr_report():
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_WITH_REVIEWS])
        generator = GitHubPrReportGenerator("org/repo", "main")
        report = generator.get_pr_report()

    assert isinstance(report, list)
    assert len(report) > 0
    assert "org/repo" in report[0]


def test_post_filter_removes_non_matching_states():
    """Reviews with states not in the filter list should be removed."""
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_MIXED_REVIEWS])
        generator = GitHubPrReportGenerator("org/repo", "main")
        report = generator.get_pr_report()

    # COMMENTED state is not in the default filter, so only APPROVED review remains
    assert any("alice" in line for line in report)
    assert not any("bob" in line for line in report)


def test_post_filter_custom_states():
    """Custom review_states_filter should be respected."""
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_MIXED_REVIEWS])
        generator = GitHubPrReportGenerator("org/repo", "main", review_states_filter=["COMMENTED"])
        report = generator.get_pr_report()

    # Only COMMENTED reviews pass the filter
    assert any("bob" in line for line in report)
    assert not any("alice" in line for line in report)


def test_post_filter_keeps_no_reviews_when_all_filtered():
    """When all reviews are filtered out, the PR should show 'No reviews'."""
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_WITH_REVIEWS])
        generator = GitHubPrReportGenerator("org/repo", "main", review_states_filter=["CHANGES_REQUESTED"])
        report = generator.get_pr_report()

    assert any("No reviews" in line for line in report)


def test_post_filter_directly():
    """Call _post_filter directly to verify it mutates reviews in-place."""
    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([])
        generator = GitHubPrReportGenerator("org/repo", "main")

    pr = PrMerge.from_dict(PR_DICT_MIXED_REVIEWS)
    data = PrReportData(repo="org/repo", branch="main", pr_merges=[pr])
    filtered = generator._post_filter(data)  # noqa: SLF001

    assert len(filtered.pr_merges[0].reviews) == 1
    assert filtered.pr_merges[0].reviews[0].state == "APPROVED"


# ---------------------------------------------------------------------------
# generate_pr_approvals_md
# ---------------------------------------------------------------------------


def test_generate_pr_approvals_md(tmp_path):
    output_file = str(tmp_path / "report.md")

    with patch("tgedr_pycommons.cicd.pr_report_generator.subprocess.run") as mock_run:
        mock_run.return_value = _make_gh_response([PR_DICT_WITH_REVIEWS])
        generate_pr_approvals_md("org/repo", "main", output_file, max_prs=10)

    content = Path(output_file).read_text(encoding="utf-8")
    assert "org/repo" in content
    assert "feat: add feature" in content


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main(tmp_path):
    output_file = str(tmp_path / "approvals.md")

    with patch(
        "tgedr_pycommons.cicd.pr_report_generator.subprocess.run"
    ) as mock_run, patch(
        "sys.argv",
        ["prog", "--repo", "org/repo", "--output", output_file, "--branch", "main", "--maxprs", "50"],
    ):
        mock_run.return_value = _make_gh_response([PR_DICT_NO_REVIEWS])
        main()

    content = Path(output_file).read_text(encoding="utf-8")
    assert "org/repo" in content


def test_main_defaults(tmp_path, monkeypatch):
    output_file = str(tmp_path / "approvals.md")
    monkeypatch.chdir(tmp_path)

    with patch(
        "tgedr_pycommons.cicd.pr_report_generator.subprocess.run"
    ) as mock_run, patch(
        "sys.argv",
        ["prog", "--repo", "org/repo", "--output", output_file],
    ):
        mock_run.return_value = _make_gh_response([])
        main()

    content = Path(output_file).read_text(encoding="utf-8")
    assert "org/repo" in content
