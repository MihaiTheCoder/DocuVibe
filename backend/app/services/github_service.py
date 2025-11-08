"""
GitHub Integration Service
"""

import httpx
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import logging

from app.core.config import settings
from app.models.github_integration import IssueDifficulty, IssueStatus

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub API integration"""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO

        if not self.token:
            raise ValueError("GITHUB_TOKEN not configured")

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        difficulty: IssueDifficulty
    ) -> Dict[str, Any]:
        """
        Create a GitHub issue

        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of labels to apply
            difficulty: Difficulty level (easy/medium/hard)

        Returns:
            GitHub issue data including number and URL
        """
        # Add difficulty label
        labels.append(difficulty.value)

        # Format issue body with lazy-bird compatibility
        formatted_body = self._format_issue_body(body, difficulty)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{self.repo}/issues",
                headers=self.headers,
                json={
                    "title": title,
                    "body": formatted_body,
                    "labels": labels
                }
            )

            if response.status_code != 201:
                raise Exception(f"Failed to create issue: {response.text}")

            data = response.json()
            return {
                "number": data["number"],
                "url": data["html_url"],
                "id": data["id"],
                "node_id": data["node_id"]
            }

    async def add_ready_label(self, issue_number: int) -> bool:
        """
        Add 'ready' label to trigger lazy-bird processing

        Args:
            issue_number: GitHub issue number

        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels",
                headers=self.headers,
                json={"labels": ["ready"]}
            )

            return response.status_code == 200

    async def get_issue_status(self, issue_number: int) -> Dict[str, Any]:
        """
        Get current status of an issue

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue status information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{self.repo}/issues/{issue_number}",
                headers=self.headers
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get issue: {response.text}")

            data = response.json()

            # Check for linked PRs
            pr_info = await self._get_linked_pr(issue_number)

            return {
                "state": data["state"],
                "labels": [label["name"] for label in data["labels"]],
                "has_pr": pr_info is not None,
                "pr_number": pr_info["number"] if pr_info else None,
                "pr_url": pr_info["html_url"] if pr_info else None,
                "pr_state": pr_info["state"] if pr_info else None
            }

    async def get_pr_status(self, pr_number: int) -> Dict[str, Any]:
        """
        Get PR status including checks and reviews

        Args:
            pr_number: Pull request number

        Returns:
            PR status information
        """
        async with httpx.AsyncClient() as client:
            # Get PR details
            pr_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}",
                headers=self.headers
            )

            if pr_response.status_code != 200:
                raise Exception(f"Failed to get PR: {pr_response.text}")

            pr_data = pr_response.json()

            # Get check runs
            checks_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/commits/{pr_data['head']['sha']}/check-runs",
                headers=self.headers
            )

            checks_data = checks_response.json() if checks_response.status_code == 200 else {"check_runs": []}

            # Get reviews
            reviews_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/reviews",
                headers=self.headers
            )

            reviews_data = reviews_response.json() if reviews_response.status_code == 200 else []

            return {
                "state": pr_data["state"],
                "mergeable": pr_data.get("mergeable"),
                "merged": pr_data.get("merged", False),
                "checks_passing": self._are_checks_passing(checks_data["check_runs"]),
                "approved": self._is_approved(reviews_data),
                "head_sha": pr_data["head"]["sha"]
            }

    async def enable_auto_merge(self, pr_number: int) -> bool:
        """
        Enable auto-merge for a PR (requires GraphQL API)

        Args:
            pr_number: Pull request number

        Returns:
            True if successful
        """
        # Get PR node ID first
        async with httpx.AsyncClient() as client:
            pr_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}",
                headers=self.headers
            )

            if pr_response.status_code != 200:
                return False

            pr_data = pr_response.json()
            node_id = pr_data["node_id"]

            # Use GraphQL to enable auto-merge
            graphql_query = """
            mutation EnableAutoMerge($pullRequestId: ID!) {
                enablePullRequestAutoMerge(input: {
                    pullRequestId: $pullRequestId,
                    mergeMethod: SQUASH
                }) {
                    pullRequest {
                        autoMergeRequest {
                            enabledAt
                        }
                    }
                }
            }
            """

            response = await client.post(
                f"{self.base_url}/graphql",
                headers=self.headers,
                json={
                    "query": graphql_query,
                    "variables": {"pullRequestId": node_id}
                }
            )

            return response.status_code == 200

    async def merge_pr(self, pr_number: int, commit_message: str = None) -> bool:
        """
        Manually merge a PR

        Args:
            pr_number: Pull request number
            commit_message: Optional custom commit message

        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/merge",
                headers=self.headers,
                json={
                    "merge_method": "squash",
                    "commit_title": commit_message or f"Merge PR #{pr_number}",
                    "commit_message": "Auto-merged by VibeDocs Chat UI"
                }
            )

            return response.status_code == 200

    async def _get_linked_pr(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Find PR linked to an issue

        Args:
            issue_number: Issue number

        Returns:
            PR data if found, None otherwise
        """
        async with httpx.AsyncClient() as client:
            # Search for PRs that reference this issue
            search_response = await client.get(
                f"{self.base_url}/search/issues",
                headers=self.headers,
                params={
                    "q": f"repo:{self.repo} is:pr #{issue_number} in:body"
                }
            )

            if search_response.status_code == 200:
                data = search_response.json()
                if data["total_count"] > 0:
                    return data["items"][0]

            return None

    def _format_issue_body(self, body: str, difficulty: IssueDifficulty) -> str:
        """
        Format issue body for lazy-bird compatibility

        Args:
            body: Original issue body
            difficulty: Issue difficulty

        Returns:
            Formatted body with metadata and structure
        """
        return f"""## Feature Request

{body}

## Implementation Details

**Difficulty**: {difficulty.value}
**Auto-generated**: Yes
**Source**: VibeDocs Chat UI

## Acceptance Criteria

- [ ] Feature implemented according to specification
- [ ] Unit tests added and passing
- [ ] Integration tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated if necessary

## Technical Notes

This issue was automatically created from a user feature request via the VibeDocs Chat UI.
It has been classified as **{difficulty.value}** based on complexity analysis.

{'' if difficulty != IssueDifficulty.EASY else '**Note**: This issue is marked for automatic merging after successful tests.'}

---
*Generated by VibeDocs Chat UI*
"""

    def _are_checks_passing(self, check_runs: List[Dict[str, Any]]) -> bool:
        """
        Check if all CI checks are passing

        Args:
            check_runs: List of check run data

        Returns:
            True if all checks pass
        """
        if not check_runs:
            return True  # No checks configured

        for check in check_runs:
            if check["status"] != "completed":
                return False
            if check["conclusion"] not in ["success", "neutral", "skipped"]:
                return False

        return True

    def _is_approved(self, reviews: List[Dict[str, Any]]) -> bool:
        """
        Check if PR has required approvals

        Args:
            reviews: List of review data

        Returns:
            True if approved
        """
        # Get latest review from each user
        user_reviews = {}
        for review in reviews:
            user = review["user"]["login"]
            if user not in user_reviews or review["submitted_at"] > user_reviews[user]["submitted_at"]:
                user_reviews[user] = review

        # Check if any review is approved
        for review in user_reviews.values():
            if review["state"] == "APPROVED":
                return True

        return False
