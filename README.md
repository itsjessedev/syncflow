# SyncFlow

Automated sync between Salesforce, Jira, and Google Sheets. Eliminates hours of manual CSV exports and copy-pasting.

## Problem

Businesses waste hours weekly exporting CSVs from multiple platforms to update a "master sheet" for reporting. Sales data lives in Salesforce, project tasks in Jira, and executives want everything in one Google Sheet.

## Solution

SyncFlow automatically pulls data from Salesforce and Jira APIs, transforms and merges it, and updates Google Sheets on a configurable schedule.

## Features

- **Real-time sync dashboard** - Monitor sync status and history
- **Conflict resolution** - Configurable rules for when sources disagree
- **Email alerts** - Get notified on sync failures
- **Historical logs** - Full audit trail of all syncs
- **Flexible scheduling** - Cron-based, run every hour or once daily

## Tech Stack

- Python 3.11+
- FastAPI (dashboard API)
- Salesforce REST API
- Jira REST API
- Google Sheets API
- SQLite (sync history)
- APScheduler (cron jobs)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/itsjessedev/syncflow.git
cd syncflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API credentials

# Run the dashboard
python -m src.main

# Or run a one-time sync
python -m src.sync
```

## Configuration

See `.env.example` for all configuration options:

- Salesforce credentials and SOQL query
- Jira credentials and JQL filter
- Google Sheets API credentials and spreadsheet ID
- Sync schedule (cron expression)
- Email notification settings

## Demo Mode

Run with mock data (no API credentials needed):

```bash
DEMO_MODE=true python -m src.main
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/status` | GET | Current sync status |
| `/api/history` | GET | Sync history |
| `/api/sync` | POST | Trigger manual sync |
| `/api/config` | GET/PUT | View/update configuration |

## Project Structure

```
syncflow/
├── src/
│   ├── api/           # FastAPI routes
│   ├── services/      # Salesforce, Jira, Sheets integrations
│   ├── utils/         # Helpers, logging, email
│   └── main.py        # Application entry
├── tests/             # Unit and integration tests
├── config/            # Configuration schemas
├── scripts/           # Deployment scripts
└── docker-compose.yml # Container deployment
```

## Results

> "Saved our 4-person sales team 6 hours per week. The master sheet updates automatically every morning before our standup."

## License

MIT
