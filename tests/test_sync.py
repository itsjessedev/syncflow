"""Tests for the sync service."""

import os
import pytest

# Enable demo mode for tests
os.environ["DEMO_MODE"] = "true"

from src.services.sync import sync_service, SyncStatus
from src.services.salesforce import salesforce_service
from src.services.jira_service import jira_service


class TestSalesforceService:
    """Tests for Salesforce integration."""

    def test_connect_demo_mode(self):
        """Test connection in demo mode."""
        assert salesforce_service.connect() is True

    def test_fetch_opportunities_demo_mode(self):
        """Test fetching opportunities in demo mode."""
        salesforce_service.connect()
        opps = salesforce_service.fetch_opportunities()
        assert len(opps) > 0
        assert "Id" in opps[0]
        assert "Name" in opps[0]


class TestJiraService:
    """Tests for Jira integration."""

    def test_connect_demo_mode(self):
        """Test connection in demo mode."""
        assert jira_service.connect() is True

    def test_fetch_issues_demo_mode(self):
        """Test fetching issues in demo mode."""
        jira_service.connect()
        issues = jira_service.fetch_issues()
        assert len(issues) > 0
        assert "key" in issues[0]
        assert "summary" in issues[0]


class TestSyncService:
    """Tests for the main sync orchestration."""

    def test_run_sync_demo_mode(self):
        """Test running a full sync in demo mode."""
        result = sync_service.run_sync()

        assert result.status in [SyncStatus.SUCCESS, SyncStatus.PARTIAL]
        assert result.salesforce_records > 0
        assert result.jira_issues > 0
        assert result.completed_at is not None

    def test_sync_history(self):
        """Test that sync history is recorded."""
        initial_count = len(sync_service.history)
        sync_service.run_sync()
        assert len(sync_service.history) > initial_count

    def test_result_to_dict(self):
        """Test result serialization."""
        result = sync_service.run_sync()
        data = result.to_dict()

        assert "status" in data
        assert "started_at" in data
        assert "salesforce_records" in data
        assert "duration_seconds" in data
