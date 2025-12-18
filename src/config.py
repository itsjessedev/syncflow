"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Settings
    demo_mode: bool = Field(default=False, description="Run with mock data")
    debug: bool = Field(default=False, description="Enable debug logging")

    # Salesforce
    sf_username: str = Field(default="", description="Salesforce username")
    sf_password: str = Field(default="", description="Salesforce password")
    sf_security_token: str = Field(default="", description="Salesforce security token")
    sf_domain: str = Field(default="login", description="Salesforce domain")
    sf_query: str = Field(
        default="SELECT Id, Name, Amount, StageName, CloseDate FROM Opportunity WHERE IsClosed = false",
        description="SOQL query to fetch data"
    )

    # Jira
    jira_url: str = Field(default="", description="Jira instance URL")
    jira_email: str = Field(default="", description="Jira email")
    jira_api_token: str = Field(default="", description="Jira API token")
    jira_jql: str = Field(
        default="project = SALES ORDER BY created DESC",
        description="JQL query to fetch issues"
    )

    # Google Sheets
    google_credentials_file: str = Field(default="credentials.json")
    google_spreadsheet_id: str = Field(default="")
    google_sheet_name: str = Field(default="Master Data")

    # Sync Schedule
    sync_schedule: str = Field(default="0 7 * * *", description="Cron schedule")

    # Email
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    notify_email: str = Field(default="")

    # Conflict Resolution
    conflict_strategy: Literal["salesforce_wins", "jira_wins", "most_recent", "manual"] = Field(
        default="salesforce_wins"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
