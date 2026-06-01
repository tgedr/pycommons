"""PR Report Generator module.

Provides functionality to fetch merged pull requests from GitHub and generate
markdown reports summarizing PR approvals and review information.

Example:
    `uv run python src/tgedr_pycommons/cicd/pr_report_generator.py --repo jtviegas/bashutils --branch master --output approvals.md`
    `uv run python -c "from tgedr_pycommons.cicd.pr_report_generator import generate_pr_approvals_md; generate_pr_approvals_md('jtviegas/bashutils', 'master', 'pr_approvals.md')"`

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import subprocess # nosec B404
from typing import Any, ClassVar
import argparse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class PrReview:
    """Represents a review on a pull request.

    Attributes:
        id: The unique identifier of the review.
        author: The login name of the reviewer.
        submitted_at: The timestamp when the review was submitted.
        state: The state of the review (APPROVED, CHANGES_REQUESTED, DISMISSED, etc.).
    """

    id: str
    author: str
    submitted_at: str
    state: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "PrReview":
        """Create a PrReview instance from a dictionary.

        Args:
            d: Dictionary containing review data with keys: id, author, submittedAt, state.

        Returns:
            A PrReview instance populated from the dictionary data.
        """
        return PrReview(
            id=d["id"],
            author=d["author"]["login"],
            submitted_at=d["submittedAt"],
            state=d["state"],
        )

@dataclass
class PrMerge:
    """Represents a merged pull request with review details.

    Attributes:
        number: The PR number.
        title: The title of the pull request.
        url: The URL of the pull request.
        merged_at: The timestamp when the PR was merged.
        merge_commit_id: The commit SHA of the merge commit.
        reviews: List of reviews on the pull request.
    """

    number: int
    title: str
    url: str
    merged_at: str
    merge_commit_id: str
    reviews: list[PrReview]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "PrMerge":
        """Create a PrMerge instance from a dictionary.

        Args:
            d: Dictionary containing PR data with keys: number, title, url, mergedAt, mergeCommit, reviews.

        Returns:
            A PrMerge instance populated from the dictionary data.
        """
        return PrMerge(
            number=d["number"],
            title=d["title"],
            url=d["url"],
            merged_at=d["mergedAt"],
            merge_commit_id=d["mergeCommit"]["oid"],
            reviews=[PrReview.from_dict(r) for r in d["reviews"]],
        )

@dataclass
class PrReportData:
    """Data class to hold PR report information."""

    repo: str
    branch: str
    pr_merges: list[PrMerge]

class PrReportGeneratorStrategy(ABC):
    """Abstract base class for PR report generation strategies.

    Defines the interface for generating markdown reports of PR approvals.
    """

    @abstractmethod
    def generate_report(self, data: PrReportData) -> list[str]:
        """Generate a markdown report of PR approvals for a repository branch.

        Args:
            data: A PRReportData object containing PR and review information.

        Returns:
            A list of strings representing formatted markdown report lines.
        """

    @staticmethod
    def get_instance(name: str | None) -> "PrReportGeneratorStrategy":  # noqa: ARG004
        """Get an instance of the default PR report generator strategy."""
        return DefaultPrReportGeneratorStrategy()

class DefaultPrReportGeneratorStrategy(PrReportGeneratorStrategy):
    """Default implementation of PrReportGeneratorStrategy.

    Generates a markdown report of PR approvals for a repository branch.
    """

    def generate_report(self, data: PrReportData) -> list[str]:
        """Generate a markdown report of PR approvals for a repository branch.

        Args:
            data: A PRReportData object containing PR and review information.

        Returns:
            A list of strings representing formatted markdown report lines.
        """
        logger.info(f"[generate_report|in] ({data})")  # noqa: G004
        result: list[str] = []

        result.append(f"# PR Approvals for repository: {data.repo} (branch: {data.branch})")
        for pr in data.pr_merges:
            result.append(f"## PR #{pr.number}: {pr.title}")
            result.append(f"- URL: {pr.url}")
            result.append(f"- Merged at: {pr.merged_at}")
            result.append(f"- Merge commit id: {pr.merge_commit_id}")
            if pr.reviews:
                result.append("- Reviews:")
                for review in pr.reviews:
                    result.append(f"  - [id: {review.id}] {review.author} - {review.state} at {review.submitted_at}")  # noqa: PERF401
            else:
                result.append("- No reviews")

        logger.info("[generate_report|out] => %s", result)
        return result

class PrReportGenerator(ABC):
    """Generator for PR reports.

    Fetches merged pull requests from a repository and generates reports
    using the specified strategy.
    """

    __DEFAULT_REVIEW_STATES_FILTER: ClassVar[list[str]] = ["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]

    def __init__(
        self,
        repo: str,
        branch: str,
        max_prs: int = 5000,
        strategy: str | None = None,
        review_states_filter: list[str] | None = None,
    ) -> None:
        """Initialize the PR info fetcher.

        Args:
            repo: Repository identifier.
            branch: Branch name to fetch PRs from.
            max_prs: Maximum number of PRs to fetch. Defaults to 5000.
            strategy: Optional strategy for generating PR reports.
            review_states_filter: Optional list of states to filter PR reviews.
        """
        self._repo = repo
        self._branch = branch
        self._max_prs = max_prs
        self._strategy = PrReportGeneratorStrategy.get_instance(strategy)
        self._review_states_filter = review_states_filter if review_states_filter is not None else self.__DEFAULT_REVIEW_STATES_FILTER

    @abstractmethod
    def _get_pr_report_data(self) -> PrReportData:
        """Fetch all merged pull requests as PrMerge instances."""

    def _post_filter(self, data: PrReportData) -> PrReportData:
        for merge in data.pr_merges:
            merge.reviews = [r for r in merge.reviews if r.state in self._review_states_filter]
        return data

    def get_pr_report(self) -> list[str]:
        """Generate a markdown report summarizing PR merges and approvals."""
        logger.info("[get_pr_report|in]")
        data: PrReportData = self._get_pr_report_data()
        data = self._post_filter(data)
        result: list[str] = self._strategy.generate_report(data)
        logger.info("[get_pr_report|out] => %s", result)
        return result

class GitHubPrReportGenerator(PrReportGenerator):
    """Generator for GitHub PR reports.

    Fetches merged pull requests from a GitHub repository and generates reports
    using the specified strategy.
    """

    def _get_pr_report_data(self) -> PrReportData:
        """Fetch all merged pull requests as PrMerge instances using gh CLI."""
        logger.info("[_get_pr_report_data|in] (repo=%s, branch=%s, max_prs=%d)", self._repo, self._branch, self._max_prs)
        response = subprocess.run(  # noqa: S603 # nosec B607, B603
            [  # noqa: S607
                "gh", "pr", "list",
                "--repo", self._repo,
                "--state", "merged",
                "--base", self._branch,
                "--json", "number,title,url,mergeCommit,mergedAt,reviews",
                "--limit", str(self._max_prs),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        merges: list[PrMerge] = [PrMerge.from_dict(d) for d in json.loads(response.stdout)]
        result: PrReportData = PrReportData(
            repo=self._repo,
            branch=self._branch,
            pr_merges=merges,
        )
        logger.info("[_get_pr_report_data|out] => %s", result)
        return result




def generate_pr_approvals_md(repo: str, branch: str, output: str, max_prs: int = 5000) -> None:
    """Fetch merged PRs and generate approvals Markdown."""
    generator = GitHubPrReportGenerator(repo, branch, max_prs)
    report_rows: list[str] = generator.get_pr_report()
    with Path(output).open("w", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in report_rows)


def main() -> None:
    """Main function to process PRs and generate Markdown."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="GitHub PR approval export")
    parser.add_argument("--repo", required=True, help="Repository to fetch PRs from, format: 'owner/repo'")
    parser.add_argument("--output", default="approvals.md", help="Output Markdown filename")
    parser.add_argument("--branch", default="main", help="Branch to fetch PRs from")
    parser.add_argument("--maxprs", default="5000", help="Maximum number of PRs to fetch")
    args = parser.parse_args()

    generate_pr_approvals_md(repo=args.repo, branch=args.branch, output=args.output, max_prs=int(args.maxprs))

if __name__ == "__main__":
    main()
