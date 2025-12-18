"""Jira API integration."""

import logging
from datetime import datetime
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError

from src.config import settings

logger = logging.getLogger(__name__)


# Mock data for demo mode
MOCK_ISSUES = [
    {
        "key": "SALES-101",
        "summary": "Follow up with Acme Corp on enterprise pricing",
        "status": "In Progress",
        "assignee": "John Smith",
        "priority": "High",
        "created": "2024-01-15",
        "updated": "2024-01-28",
    },
    {
        "key": "SALES-102",
        "summary": "Prepare demo environment for TechStart",
        "status": "To Do",
        "assignee": "Sarah Johnson",
        "priority": "Medium",
        "created": "2024-01-20",
        "updated": "2024-01-25",
    },
    {
        "key": "SALES-103",
        "summary": "Draft proposal for Global Industries expansion",
        "status": "In Review",
        "assignee": "Mike Williams",
        "priority": "High",
        "created": "2024-01-22",
        "updated": "2024-01-29",
    },
    {
        "key": "SALES-104",
        "summary": "Schedule kick-off call with StartupXYZ",
        "status": "Done",
        "assignee": "John Smith",
        "priority": "Low",
        "created": "2024-01-10",
        "updated": "2024-01-18",
    },
    {
        "key": "SALES-105",
        "summary": "Legal review for MegaCorp contract",
        "status": "Blocked",
        "assignee": "Legal Team",
        "priority": "Critical",
        "created": "2024-01-25",
        "updated": "2024-01-30",
    },
]


class JiraService:
    """Service for interacting with Jira API."""

    def __init__(self):
        self._client: JIRA | None = None

    def connect(self) -> bool:
        """Establish connection to Jira."""
        if settings.demo_mode:
            logger.info("Demo mode: Using mock Jira data")
            return True

        try:
            self._client = JIRA(
                server=settings.jira_url,
                basic_auth=(settings.jira_email, settings.jira_api_token),
            )
            # Test connection
            self._client.myself()
            logger.info("Connected to Jira successfully")
            return True
        except JIRAError as e:
            logger.error(f"Jira authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            return False

    def fetch_issues(self) -> list[dict[str, Any]]:
        """Fetch issues using configured JQL query."""
        if settings.demo_mode:
            logger.info(f"Demo mode: Returning {len(MOCK_ISSUES)} mock issues")
            return MOCK_ISSUES

        if not self._client:
            raise RuntimeError("Not connected to Jira. Call connect() first.")

        try:
            issues = self._client.search_issues(
                settings.jira_jql,
                maxResults=100,
                fields="key,summary,status,assignee,priority,created,updated",
            )

            results = []
            for issue in issues:
                results.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": str(issue.fields.status),
                    "assignee": str(issue.fields.assignee) if issue.fields.assignee else "Unassigned",
                    "priority": str(issue.fields.priority) if issue.fields.priority else "None",
                    "created": issue.fields.created[:10],
                    "updated": issue.fields.updated[:10],
                })

            logger.info(f"Fetched {len(results)} issues from Jira")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch issues: {e}")
            raise

    def get_last_modified(self, issue_key: str) -> datetime | None:
        """Get the last modified timestamp for an issue."""
        if settings.demo_mode:
            return datetime.now()

        if not self._client:
            return None

        try:
            issue = self._client.issue(issue_key, fields="updated")
            return datetime.fromisoformat(
                issue.fields.updated.replace("Z", "+00:00")
            )
        except Exception as e:
            logger.warning(f"Could not get last modified date for {issue_key}: {e}")

        return None


# Singleton instance
jira_service = JiraService()
