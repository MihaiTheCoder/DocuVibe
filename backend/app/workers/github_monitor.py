"""
GitHub Monitor Worker

Monitors GitHub issues and PRs for auto-merge functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.models.github_integration import GitHubIssue, IssueStatus, IssueDifficulty
from app.services.github_service import GitHubService
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """Monitor GitHub issues and PRs for automation"""

    def __init__(self):
        self.github_service = GitHubService() if settings.GITHUB_TOKEN else None
        self.check_interval = 60  # Check every minute
        self.running = False

    async def run(self):
        """Main monitoring loop"""
        if not self.github_service:
            logger.warning("GitHub token not configured, monitor disabled")
            return

        logger.info("GitHub monitor started")
        self.running = True

        while self.running:
            try:
                await self.check_issues()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.check_interval)

    async def check_issues(self):
        """Check all active issues for updates"""
        db: Session = SessionLocal()

        try:
            # Get issues that need checking
            issues = db.query(GitHubIssue).filter(
                GitHubIssue.status.in_([
                    IssueStatus.READY.value,
                    IssueStatus.IN_PROGRESS.value,
                    IssueStatus.PR_CREATED.value,
                    IssueStatus.TESTING.value
                ])
            ).all()

            for issue in issues:
                await self.check_issue(issue, db)

            db.commit()

        except Exception as e:
            logger.error(f"Error checking issues: {e}")
            db.rollback()
        finally:
            db.close()

    async def check_issue(self, issue: GitHubIssue, db: Session):
        """
        Check individual issue status

        Args:
            issue: GitHub issue to check
            db: Database session
        """
        try:
            # Get issue status from GitHub
            status = await self.github_service.get_issue_status(issue.issue_number)

            # Check if PR was created
            if status["has_pr"] and issue.status != IssueStatus.PR_CREATED:
                issue.pr_number = status["pr_number"]
                issue.pr_url = status["pr_url"]
                issue.status = IssueStatus.PR_CREATED
                issue.pr_created_at = datetime.utcnow()

                # If easy issue, enable auto-merge
                if issue.difficulty == IssueDifficulty.EASY and issue.auto_merge_enabled:
                    await self.enable_auto_merge(issue)

            # Check PR status if we have one
            if issue.pr_number:
                await self.check_pr_status(issue, db)

            # Update issue if it's been closed
            if status["state"] == "closed" and issue.status != IssueStatus.CLOSED:
                issue.status = IssueStatus.CLOSED

        except Exception as e:
            logger.error(f"Error checking issue {issue.issue_number}: {e}")

    async def check_pr_status(self, issue: GitHubIssue, db: Session):
        """
        Check PR status and handle auto-merge

        Args:
            issue: GitHub issue with PR
            db: Database session
        """
        try:
            pr_status = await self.github_service.get_pr_status(issue.pr_number)

            # Update testing status
            if pr_status["checks_passing"] and issue.status == IssueStatus.PR_CREATED:
                issue.status = IssueStatus.TESTING

            # Check if ready to merge
            if (
                pr_status["mergeable"] and
                pr_status["checks_passing"] and
                issue.difficulty == IssueDifficulty.EASY and
                issue.auto_merge_enabled
            ):
                # For easy issues, auto-merge if checks pass
                if not settings.GITHUB_REQUIRE_APPROVAL_FOR_MERGE or pr_status["approved"]:
                    success = await self.github_service.merge_pr(
                        issue.pr_number,
                        f"Auto-merge: {issue.issue_title}"
                    )

                    if success:
                        issue.status = IssueStatus.MERGED
                        issue.merged_at = datetime.utcnow()
                        logger.info(f"Auto-merged PR #{issue.pr_number}")

            # Check if already merged
            if pr_status["merged"]:
                issue.status = IssueStatus.MERGED
                issue.merged_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error checking PR {issue.pr_number}: {e}")

    async def enable_auto_merge(self, issue: GitHubIssue):
        """
        Enable auto-merge for a PR

        Args:
            issue: GitHub issue with PR
        """
        try:
            # Wait a moment for GitHub to process the PR
            await asyncio.sleep(5)

            success = await self.github_service.enable_auto_merge(issue.pr_number)

            if success:
                logger.info(f"Enabled auto-merge for PR #{issue.pr_number}")
            else:
                logger.warning(f"Failed to enable auto-merge for PR #{issue.pr_number}")

        except Exception as e:
            logger.error(f"Error enabling auto-merge: {e}")

    async def stop(self):
        """Stop the monitor"""
        logger.info("Stopping GitHub monitor")
        self.running = False


# Function to run the monitor
async def run_github_monitor():
    """Run the GitHub monitor"""
    monitor = GitHubMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(run_github_monitor())
