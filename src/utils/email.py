"""Email notification utilities."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config import settings
from src.services.sync import SyncResult, SyncStatus

logger = logging.getLogger(__name__)


def send_sync_notification(result: SyncResult) -> bool:
    """Send email notification about sync result."""
    if not settings.notify_email or not settings.smtp_user:
        logger.info("Email notifications not configured, skipping")
        return False

    if settings.demo_mode:
        logger.info(f"Demo mode: Would send email to {settings.notify_email}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"SyncFlow: {result.status.value.upper()}"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.notify_email

        # Plain text version
        text = f"""
SyncFlow Sync Report
====================

Status: {result.status.value.upper()}
Started: {result.started_at.strftime('%Y-%m-%d %H:%M:%S')}
Completed: {result.completed_at.strftime('%Y-%m-%d %H:%M:%S') if result.completed_at else 'N/A'}

Results:
- Salesforce records: {result.salesforce_records}
- Jira issues: {result.jira_issues}
- Rows written: {result.rows_written}
- Conflicts resolved: {result.conflicts_resolved}

{f'Errors: {chr(10).join(result.errors)}' if result.errors else 'No errors'}
"""

        # HTML version
        status_color = {
            SyncStatus.SUCCESS: "#22c55e",
            SyncStatus.PARTIAL: "#f59e0b",
            SyncStatus.FAILED: "#ef4444",
        }.get(result.status, "#6b7280")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
        .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ font-size: 12px; color: #6b7280; }}
        .errors {{ background: #fef2f2; border: 1px solid #fecaca; padding: 10px; border-radius: 4px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">SyncFlow Report</h1>
            <p style="margin: 5px 0 0 0;">Status: {result.status.value.upper()}</p>
        </div>
        <div class="content">
            <p><strong>Time:</strong> {result.started_at.strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="stat">
                <div class="stat-value">{result.salesforce_records}</div>
                <div class="stat-label">Salesforce Records</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.jira_issues}</div>
                <div class="stat-label">Jira Issues</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.rows_written}</div>
                <div class="stat-label">Rows Written</div>
            </div>

            {f'<div class="errors"><strong>Errors:</strong><br>{"<br>".join(result.errors)}</div>' if result.errors else ''}
        </div>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, settings.notify_email, msg.as_string())

        logger.info(f"Sent notification email to {settings.notify_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False
