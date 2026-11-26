# LogisticsUpdate AI – Setup & Installation Guide

This document provides complete instructions for setting up, configuring, and running the **LogisticsUpdate AI** platform on your local machine.

---

## 1. Prerequisites

- **Operating System**: macOS, Linux, or Windows (WSL recommended)
- **Python Version**: Python 3.10+ (tested on Python 3.11, 3.12, 3.13)
- **Git** installed on your system
- Modern web browser (Chrome, Safari, Firefox, Edge)

---

## 2. Step-by-Step Installation

### Step 2.1: Clone or Navigate to the Repository
```bash
cd "/Users/makinenibasavagayathri/gen ai project"
```

### Step 2.2: Set Up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2.3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Environment Configuration

Copy the template `.env.example` to create your active `.env` file:
```bash
cp .env.example .env
```

Open `.env` only if you want to configure optional integrations:

```ini
# Web Scraping Service: Firecrawl API Key (https://www.firecrawl.dev)
FIRECRAWL_API_KEY=

# Memento Historical Memory Provider
MEMENTO_API_KEY=
MEMENTO_API_URL=https://api.memento.ai/v1

# Database URL (SQLite)
DATABASE_URL=sqlite:///./database/app.db
```

The 24-hour weather forecast uses live Open-Meteo public data and needs no API key. NOAA severe weather alerts are also collected from its public API. Add a Firecrawl key only if you want to scrape the other configured websites. Operational reports are generated locally from recorded data and do not require an AI provider or API key; they are template-based, not generative AI.

The historical-event database starts empty and there is no bundled labeled training dataset. Add only source-backed precedents with their actual operational response and observed outcome. The 24-hour weather index is rule-based and is not a trained prediction model.

---

## 4. Database Initialization

Initialize the SQLite schema and register the default public monitoring sources:
```bash
python -c "from database.db import init_db; init_db()"
```
This creates:
- `database/app.db` with all 6 tables (`disruptions`, `historical_events`, `operational_responses`, `sources`, `reports`, `collection_logs`).

---

## 5. Running the Application

### 5.1 Start the FastAPI application
```bash
./run.sh
```
The script opens the operations dashboard in your browser. The dashboard and REST API are served by the same process:
- Dashboard: `http://127.0.0.1:8000/`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

Verify the API is live:
```bash
curl http://127.0.0.1:8000/api/health
# Output: {"status":"ok","service":"LogisticsUpdate AI Backend","version":"1.0.0"}
```

---

## 6. Running the Test Suite

Run all automated unit and integration tests:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```
The tests mock public providers and write generated snapshots to temporary test directories.

---

## 7. Troubleshooting & FAQs

- **Port 8000 already in use?**
  Start FastAPI on another port: `uvicorn app.main:app --port 8080 --reload`, then open `http://127.0.0.1:8080/`.
- **Database schema changes?**
  Delete `database/app.db` and re-run `python -c "from database.db import init_db; init_db()"`.
