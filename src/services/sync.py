"""Main sync orchestration logic."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.config import settings
from src.services.salesforce import salesforce_service
from src.services.jira_service import jira_service
from src.services.sheets import sheets_service

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Status of a sync operation."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    status: SyncStatus
    started_at: datetime
    completed_at: datetime | None = None
    salesforce_records: int = 0
    jira_issues: int = 0
    rows_written: int = 0
    conflicts_resolved: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "salesforce_records": self.salesforce_records,
            "jira_issues": self.jira_issues,
            "rows_written": self.rows_written,
            "conflicts_resolved": self.conflicts_resolved,
            "errors": self.errors,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),
        }


class SyncService:
    """Orchestrates the sync between Salesforce, Jira, and Google Sheets."""

    def __init__(self):
        self._last_result: SyncResult | None = None
        self._history: list[SyncResult] = []

    @property
    def last_result(self) -> SyncResult | None:
        return self._last_result

    @property
    def history(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._history[-50:]]  # Last 50 syncs

    def run_sync(self) -> SyncResult:
        """Execute a full sync operation."""
        result = SyncResult(
            status=SyncStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            # Connect to all services
            logger.info("Starting sync operation...")

            if not salesforce_service.connect():
                result.errors.append("Failed to connect to Salesforce")

            if not jira_service.connect():
                result.errors.append("Failed to connect to Jira")

            if not sheets_service.connect():
                result.errors.append("Failed to connect to Google Sheets")

            # Fetch data from sources
            opportunities = []
            issues = []

            try:
                opportunities = salesforce_service.fetch_opportunities()
                result.salesforce_records = len(opportunities)
            except Exception as e:
                result.errors.append(f"Salesforce fetch error: {e}")

            try:
                issues = jira_service.fetch_issues()
                result.jira_issues = len(issues)
            except Exception as e:
                result.errors.append(f"Jira fetch error: {e}")

            # Transform and merge data
            merged_data = self._merge_data(opportunities, issues)
            result.conflicts_resolved = merged_data.get("conflicts", 0)

            # Write to sheet
            sheet_data = self._format_for_sheet(merged_data["rows"])
            try:
                result.rows_written = sheets_service.write_sheet(sheet_data)
            except Exception as e:
                result.errors.append(f"Sheets write error: {e}")

            # Determine final status
            if result.errors:
                result.status = SyncStatus.PARTIAL if result.rows_written > 0 else SyncStatus.FAILED
            else:
                result.status = SyncStatus.SUCCESS

        except Exception as e:
            logger.exception("Sync failed with unexpected error")
            result.status = SyncStatus.FAILED
            result.errors.append(f"Unexpected error: {e}")

        result.completed_at = datetime.now()
        self._last_result = result
        self._history.append(result)

        logger.info(
            f"Sync completed: {result.status.value} - "
            f"{result.salesforce_records} SF records, "
            f"{result.jira_issues} Jira issues, "
            f"{result.rows_written} rows written"
        )

        return result

    def _merge_data(
        self,
        opportunities: list[dict],
        issues: list[dict]
    ) -> dict[str, Any]:
        """Merge Salesforce and Jira data with conflict resolution."""
        rows = []
        conflicts = 0

        # Create a mapping of opportunity names to Jira issues
        # This is a simplified example - real implementation would use
        # configurable matching logic
        opp_name_to_issue = {}
        for issue in issues:
            # Extract company name from issue summary (simplified)
            for opp in opportunities:
                if opp["Name"].split(" - ")[0].lower() in issue["summary"].lower():
                    opp_name_to_issue[opp["Id"]] = issue
                    break

        for opp in opportunities:
            row = {
                "source": "Combined",
                "sf_id": opp["Id"],
                "name": opp["Name"],
                "amount": opp.get("Amount", 0),
                "stage": opp.get("StageName", ""),
                "close_date": opp.get("CloseDate", ""),
                "jira_key": "",
                "jira_status": "",
                "jira_assignee": "",
                "last_updated": datetime.now().isoformat(),
            }

            # Merge Jira data if available
            if opp["Id"] in opp_name_to_issue:
                issue = opp_name_to_issue[opp["Id"]]
                row["jira_key"] = issue["key"]
                row["jira_status"] = issue["status"]
                row["jira_assignee"] = issue["assignee"]

                # Check for conflicts (e.g., status mismatch)
                if (opp.get("StageName") == "Closed Won" and
                    issue["status"] != "Done"):
                    conflicts += 1
                    # Apply conflict resolution strategy
                    if settings.conflict_strategy == "salesforce_wins":
                        pass  # Keep SF data as-is
                    elif settings.conflict_strategy == "jira_wins":
                        row["stage"] = issue["status"]

            rows.append(row)

        # Add Jira issues that don't match any opportunity
        matched_keys = {opp_name_to_issue.get(o["Id"], {}).get("key") for o in opportunities}
        for issue in issues:
            if issue["key"] not in matched_keys:
                rows.append({
                    "source": "Jira Only",
                    "sf_id": "",
                    "name": issue["summary"],
                    "amount": 0,
                    "stage": "",
                    "close_date": "",
                    "jira_key": issue["key"],
                    "jira_status": issue["status"],
                    "jira_assignee": issue["assignee"],
                    "last_updated": datetime.now().isoformat(),
                })

        return {"rows": rows, "conflicts": conflicts}

    def _format_for_sheet(self, rows: list[dict]) -> list[list[Any]]:
        """Format merged data for Google Sheets."""
        if not rows:
            return []

        # Header row
        headers = [
            "Source", "SF ID", "Name", "Amount", "Stage",
            "Close Date", "Jira Key", "Jira Status", "Assignee", "Last Synced"
        ]

        # Data rows
        sheet_rows = [headers]
        for row in rows:
            sheet_rows.append([
                row.get("source", ""),
                row.get("sf_id", ""),
                row.get("name", ""),
                row.get("amount", 0),
                row.get("stage", ""),
                row.get("close_date", ""),
                row.get("jira_key", ""),
                row.get("jira_status", ""),
                row.get("jira_assignee", ""),
                row.get("last_updated", ""),
            ])

        return sheet_rows


# Singleton instance
sync_service = SyncService()
