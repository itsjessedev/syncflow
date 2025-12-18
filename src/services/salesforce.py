"""Salesforce API integration."""

import logging
from datetime import datetime
from typing import Any

from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed

from src.config import settings

logger = logging.getLogger(__name__)


# Mock data for demo mode
MOCK_OPPORTUNITIES = [
    {
        "Id": "0061234567890ABCD1",
        "Name": "Acme Corp - Enterprise License",
        "Amount": 50000.00,
        "StageName": "Negotiation",
        "CloseDate": "2024-02-15",
    },
    {
        "Id": "0061234567890ABCD2",
        "Name": "TechStart Inc - Annual Contract",
        "Amount": 24000.00,
        "StageName": "Proposal",
        "CloseDate": "2024-02-28",
    },
    {
        "Id": "0061234567890ABCD3",
        "Name": "Global Industries - Q1 Expansion",
        "Amount": 125000.00,
        "StageName": "Discovery",
        "CloseDate": "2024-03-31",
    },
    {
        "Id": "0061234567890ABCD4",
        "Name": "StartupXYZ - Pilot Program",
        "Amount": 5000.00,
        "StageName": "Closed Won",
        "CloseDate": "2024-01-20",
    },
    {
        "Id": "0061234567890ABCD5",
        "Name": "MegaCorp - Multi-year Deal",
        "Amount": 500000.00,
        "StageName": "Qualification",
        "CloseDate": "2024-06-30",
    },
]


class SalesforceService:
    """Service for interacting with Salesforce API."""

    def __init__(self):
        self._client: Salesforce | None = None

    def connect(self) -> bool:
        """Establish connection to Salesforce."""
        if settings.demo_mode:
            logger.info("Demo mode: Using mock Salesforce data")
            return True

        try:
            self._client = Salesforce(
                username=settings.sf_username,
                password=settings.sf_password,
                security_token=settings.sf_security_token,
                domain=settings.sf_domain,
            )
            logger.info("Connected to Salesforce successfully")
            return True
        except SalesforceAuthenticationFailed as e:
            logger.error(f"Salesforce authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            return False

    def fetch_opportunities(self) -> list[dict[str, Any]]:
        """Fetch opportunities using configured SOQL query."""
        if settings.demo_mode:
            logger.info(f"Demo mode: Returning {len(MOCK_OPPORTUNITIES)} mock opportunities")
            return MOCK_OPPORTUNITIES

        if not self._client:
            raise RuntimeError("Not connected to Salesforce. Call connect() first.")

        try:
            result = self._client.query(settings.sf_query)
            records = result.get("records", [])

            # Remove Salesforce metadata from records
            cleaned = []
            for record in records:
                clean_record = {k: v for k, v in record.items() if k != "attributes"}
                cleaned.append(clean_record)

            logger.info(f"Fetched {len(cleaned)} opportunities from Salesforce")
            return cleaned
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            raise

    def get_last_modified(self, record_id: str) -> datetime | None:
        """Get the last modified timestamp for a record."""
        if settings.demo_mode:
            return datetime.now()

        if not self._client:
            return None

        try:
            result = self._client.query(
                f"SELECT LastModifiedDate FROM Opportunity WHERE Id = '{record_id}'"
            )
            if result.get("records"):
                return datetime.fromisoformat(
                    result["records"][0]["LastModifiedDate"].replace("Z", "+00:00")
                )
        except Exception as e:
            logger.warning(f"Could not get last modified date for {record_id}: {e}")

        return None


# Singleton instance
salesforce_service = SalesforceService()
