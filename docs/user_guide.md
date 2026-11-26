# LogisticsUpdate AI – User Guide & Quickstart

## 1. Quickstart (Local Launch)

### Prerequisites
- macOS / Linux with Python 3.10+ (Python 3.13 supported)
- Virtual environment with dependencies installed

### Launching the Operations Center
From the project folder, run:
```bash
./run.sh
```
This starts the server and opens the dashboard in your browser. If it does not open automatically, visit `http://127.0.0.1:8000/`. The API health check is available at:
```bash
curl http://127.0.0.1:8000/api/health
# Returns: {"status": "ok"}
```

Open the dashboard at `http://127.0.0.1:8000/` and interactive API docs at `http://127.0.0.1:8000/docs`.

---

## 2. Navigating the Operations Dashboard

1. **📊 Overview**: View total disruptions, critical alerts, monitored feeds, and severity distribution charts.
2. **24h Risk Forecast**: Review live weather exposure data for major logistics hubs. The page displays the additive scoring weights and risk bands; this is a rule-based index, not a trained probability model.
3. **⚡ Live Disruptions**: Filter actual alerts by severity, category, or search keywords. Generate a local evidence-based operational report for an event.
4. **📡 Data Collection**: Collect NOAA severe alerts and, when configured, scrape live public feeds with Firecrawl. Add or delete monitored feed URLs.
5. **📜 Historical Events**: Browse only stored events with source references and recorded outcomes. The store starts empty; add verified precedents to enable comparisons.
6. **🔍 Similarity & Comparison**: Compare an active disruption against stored real historical records.
7. **📋 Operational Reports**: Generate and read 13-section reports based on stored event facts and precedents. These reports use a local template, are not generative AI, and can be exported as PDF or text without an API key.
8. **⚙️ System Status**: Check integration configuration and open interactive API documentation.

---

## 3. Environment Variables (`.env`)
Create a `.env` file from `.env.example`:
```env
FIRECRAWL_API_KEY="your-firecrawl-key"  # Optional; NOAA alerts work without it
DATABASE_URL="sqlite:///database/app.db"
```
Operational reports do not use or require external AI credentials.
