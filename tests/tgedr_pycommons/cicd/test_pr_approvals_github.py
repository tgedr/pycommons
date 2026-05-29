"""Unit tests for pr_approvals_github module."""
import json
from unittest.mock import MagicMock, patch

from tgedr_pycommons.cicd.pr_approvals_github import (
    generate_pdf,
    generate_pr_approvals_pdf,
    get_approval_details,
    get_completed_prs,
    get_merge_commit_id,
    main,
)


def test_get_completed_prs():  # noqa: ANN201, D103
    mock_prs = [{"number": 1, "title": "Test PR"}]
    mock_result = MagicMock()
    mock_result.stdout = json.dumps(mock_prs)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = get_completed_prs("owner/repo", "main", 100)
    assert result == mock_prs
    mock_run.assert_called_once_with(
        [
            "gh", "pr", "list",
            "--repo", "owner/repo",
            "--state", "merged",
            "--base", "main",
            "--json", "number,title,url,mergeCommit,mergedAt,reviews",
            "--limit", "100",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_approval_details_empty_reviews():  # noqa: ANN201, D103
    assert get_approval_details({}) == []
    assert get_approval_details({"reviews": []}) == []


def test_get_approval_details_approved_with_timestamp():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "alice"}, "state": "APPROVED", "submittedAt": "2024-01-01T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- alice - Approved at 2024-01-01T00:00:00Z"]


def test_get_approval_details_approved_no_timestamp():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "alice"}, "state": "APPROVED", "submittedAt": ""},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- alice - Approved"]


def test_get_approval_details_changes_requested():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "bob"}, "state": "CHANGES_REQUESTED", "submittedAt": "2024-01-02T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- bob - Changes Requested at 2024-01-02T00:00:00Z"]


def test_get_approval_details_dismissed():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "carol"}, "state": "DISMISSED", "submittedAt": "2024-01-03T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- carol - Dismissed at 2024-01-03T00:00:00Z"]


def test_get_approval_details_ignored_state():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "dave"}, "state": "COMMENTED", "submittedAt": "2024-01-04T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == []


def test_get_approval_details_latest_review_wins():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"author": {"login": "alice"}, "state": "CHANGES_REQUESTED", "submittedAt": "2024-01-01T00:00:00Z"},
            {"author": {"login": "alice"}, "state": "APPROVED", "submittedAt": "2024-01-02T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- alice - Approved at 2024-01-02T00:00:00Z"]


def test_get_approval_details_unknown_author():  # noqa: ANN201, D103
    pr = {
        "reviews": [
            {"state": "APPROVED", "submittedAt": "2024-01-01T00:00:00Z"},
        ]
    }
    result = get_approval_details(pr)
    assert result == ["- unknown - Approved at 2024-01-01T00:00:00Z"]


def test_get_merge_commit_id_present():  # noqa: ANN201, D103
    assert get_merge_commit_id({"mergeCommit": {"oid": "abc123"}}) == "abc123"


def test_get_merge_commit_id_absent():  # noqa: ANN201, D103
    assert get_merge_commit_id({}) == ""


def test_generate_pdf_with_approvals(tmp_path):  # noqa: ANN201, D103
    prs = [
        {
            "number": 1,
            "title": "Fix bug",
            "url": "https://github.com/owner/repo/pull/1",
            "mergeCommit": {"oid": "abc123"},
            "mergedAt": "2024-01-01T00:00:00Z",
            "reviews": [
                {"author": {"login": "alice"}, "state": "APPROVED", "submittedAt": "2024-01-01T00:00:00Z"},
            ],
        }
    ]
    output = str(tmp_path / "test.pdf")
    with patch("tgedr_pycommons.cicd.pr_approvals_github.canvas.Canvas") as mock_canvas_cls:
        mock_c = MagicMock()
        mock_canvas_cls.return_value = mock_c
        generate_pdf(prs, "owner/repo", output)
    mock_canvas_cls.assert_called_once()
    mock_c.save.assert_called_once()


def test_generate_pdf_no_approvals(tmp_path):  # noqa: ANN201, D103
    prs = [
        {
            "number": 2,
            "title": "Add feature",
            "url": "https://github.com/owner/repo/pull/2",
            "mergeCommit": {"oid": "def456"},
            "mergedAt": "2024-01-02T00:00:00Z",
            "reviews": [],
        }
    ]
    output = str(tmp_path / "test.pdf")
    with patch("tgedr_pycommons.cicd.pr_approvals_github.canvas.Canvas") as mock_canvas_cls:
        mock_c = MagicMock()
        mock_canvas_cls.return_value = mock_c
        generate_pdf(prs, "owner/repo", output)
    mock_c.save.assert_called_once()


def test_generate_pdf_page_break(tmp_path):  # noqa: ANN201, D103
    """Test that page breaks occur when y coordinate drops below 60."""
    # 9 PRs with no approvals are enough to exhaust a page (each PR takes ~85pt)
    prs = [
        {
            "number": i,
            "title": f"PR {i}",
            "url": f"https://github.com/owner/repo/pull/{i}",
            "mergeCommit": {"oid": f"sha{i}"},
            "mergedAt": "2024-01-01T00:00:00Z",
            "reviews": [],
        }
        for i in range(1, 11)
    ]
    output = str(tmp_path / "test.pdf")
    with patch("tgedr_pycommons.cicd.pr_approvals_github.canvas.Canvas") as mock_canvas_cls:
        mock_c = MagicMock()
        mock_canvas_cls.return_value = mock_c
        generate_pdf(prs, "owner/repo", output)
    mock_c.showPage.assert_called()
    mock_c.save.assert_called_once()


def test_main_with_prs():  # noqa: ANN201, D103
    mock_prs = [
        {
            "number": 1,
            "title": "Test",
            "url": "https://github.com/owner/repo/pull/1",
            "mergeCommit": {"oid": "abc"},
            "mergedAt": "2024-01-01T00:00:00Z",
            "reviews": [],
        }
    ]
    with patch("sys.argv", ["prog", "--repo", "owner/repo", "--branch", "main"]):
        with patch("tgedr_pycommons.cicd.pr_approvals_github.get_completed_prs", return_value=mock_prs) as mock_get:
            with patch("tgedr_pycommons.cicd.pr_approvals_github.generate_pdf") as mock_pdf:
                main()
    mock_get.assert_called_once_with("owner/repo", "main", 5000)
    mock_pdf.assert_called_once_with(mock_prs, "owner/repo", "approvals.pdf")


def test_main_no_prs():  # noqa: ANN201, D103
    with patch("sys.argv", ["prog", "--repo", "owner/repo"]):
        with patch("tgedr_pycommons.cicd.pr_approvals_github.get_completed_prs", return_value=[]):
            with patch("tgedr_pycommons.cicd.pr_approvals_github.generate_pdf") as mock_pdf:
                main()
    mock_pdf.assert_not_called()


def test_generate_pr_approvals_pdf_with_prs():  # noqa: ANN201, D103
    mock_prs = [{"number": 1, "title": "Test", "reviews": []}]
    with patch("tgedr_pycommons.cicd.pr_approvals_github.get_completed_prs", return_value=mock_prs) as mock_get:
        with patch("tgedr_pycommons.cicd.pr_approvals_github.generate_pdf") as mock_pdf:
            generate_pr_approvals_pdf("owner/repo", "main", "out.pdf", max_prs=100)
    mock_get.assert_called_once_with("owner/repo", "main", 100)
    mock_pdf.assert_called_once_with(mock_prs, "owner/repo", "out.pdf")


def test_generate_pr_approvals_pdf_no_prs():  # noqa: ANN201, D103
    with patch("tgedr_pycommons.cicd.pr_approvals_github.get_completed_prs", return_value=[]):
        with patch("tgedr_pycommons.cicd.pr_approvals_github.generate_pdf") as mock_pdf:
            generate_pr_approvals_pdf("owner/repo", "main", "out.pdf")
    mock_pdf.assert_not_called()
