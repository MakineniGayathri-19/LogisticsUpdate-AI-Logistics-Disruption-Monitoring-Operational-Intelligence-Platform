# LogisticsUpdate AI – REST API Reference

The FastAPI backend server runs on `http://127.0.0.1:8000` with all endpoints routed under `/api`. Interactive OpenAPI documentation and test runner is available at `http://127.0.0.1:8000/docs`.

---

## 1. System Health & Diagnostics

### `GET /api/health`
Returns system operational health.
```json
{
  "status": "ok",
  "service": "LogisticsUpdate AI Backend",
  "version": "1.0.0"
}
```

### `GET /api/stats`
Returns aggregated KPI counts for the dashboard overview.
```json
{
  "total_disruptions": 12,
  "active_disruptions": 10,
  "critical_disruptions": 2,
  "high_disruptions": 4,
  "historical_stored": 6,
  "ai_reports_generated": 5,
  "sources_count": 5,
  "last_collection_time": "2026-11-22T22:54:12+00:00"
}
```

### `GET /api/memento/status`
Returns the historical event storage status. SQLite is the local authoritative store; optional cloud synchronization is not assumed to be live.
```json
{
  "status": "local_database",
  "adapter": "SQLite Historical Event Store",
  "endpoint": "database/app.db",
  "is_live": false
}
```

### `GET /api/integrations`
Returns configured integration names and readiness without exposing keys.
The response reports `"report_generator": "Local evidence-based template"` and `"report_requires_api_key": false`.

### `GET /api/forecast`
Fetches current hourly Open-Meteo data for six hubs, returns a rule-based 24-hour weather exposure index, and saves raw JSON plus processed JSON/CSV snapshots under `data/raw/` and `data/processed/`. The response's `risk_method` field lists the scoring weights and levels. The index is not a trained probability model. Returns `503` if the public forecast cannot be fetched or parsed.

---

## 2. Ingestion & Collection

### `POST /api/collect`
Triggers NOAA alert collection and optional Firecrawl website scraping, followed by Pandas cleaning and SQLite persistence. NOAA data is available without a key; other website feeds require Firecrawl configuration.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "sources_scraped": 5,
  "fetched": 2,
  "processed": 2,
  "stored": 2,
  "errors_count": 3
}
```

### `GET /api/logs?limit=25`
Retrieves auditable collection run logs.

---

## 3. Disruptions

### `GET /api/disruptions`
List all recorded disruption events ordered newest first.

### `GET /api/disruptions/{event_id}`
Retrieve complete details for a specific disruption.

### `POST /api/disruptions`
Inject or create a new disruption record.
- **Payload**:
```json
{
  "title": "Port of Long Beach Crane Malfunction",
  "description": "Container crane failure causes severe container dwell time.",
  "category": "Port Disruption",
  "location": "Long Beach, CA, USA",
  "severity": "High",
  "status": "Active",
  "source_name": "Port Authority",
  "source_url": "https://polb.com/advisory"
}
```

---

## 4. Monitoring Sources

### `GET /api/sources`
List all registered scraping and RSS feeds.

### `POST /api/sources`
Register a new URL feed for automated scraping.
- **Payload**:
```json
{
  "name": "Maritime Executive",
  "url": "https://maritime-executive.com/news",
  "category": "Port Disruption"
}
```

### `DELETE /api/sources/{source_id}`
Remove a monitoring source by ID.

---

## 5. Historical Precedents & Comparison

### `GET /api/historical-events`
List all stored historical precedents with documented responses and outcomes.

### `POST /api/historical-events`
Commit a source-backed historical event with its documented response and observed outcome to SQLite. `title`, `description`, `source_name`, `source_url`, `response`, and `outcome` are required; the source URL must be a valid HTTP(S) URL.

### `POST /api/compare/{event_id}`
Computes TF-IDF vector cosine similarity between the selected disruption and all historical precedents.
- **Response `200 OK`**:
```json
{
  "current_event": { ... },
  "similar_events": [
    {
      "similarity": 0.384,
      "similarity_percentage": 38.4,
      "title": "Port of Los Angeles Container Congestion",
      "previous_response": "Rerouted priority cargo via Oakland.",
      "historical_outcome": "Dwell time reduced by 35% within 10 days.",
      "key_differences": ["Current occurred in Rotterdam vs precedent in Los Angeles"],
      "operational_observations": ["Direct terminal congestion precedent"]
    }
  ],
  "top_match_score": 0.384
}
```

---

## 6. Operational Reports

### `POST /api/reports/generate`
Generates a 13-section report locally from the disruption record and stored historical comparisons. This template-based output is not generative AI and does not require an API key.
- **Payload**: `{"event_id": "<disruption_id>"}`
- **Response `200 OK`**:
```json
{
  "id": "a4b8e2d93e11",
  "disruption_id": "stored-disruption-id",
  "content": "LOGISTICSUPDATE — OPERATIONAL REPORT\nGenerated locally from stored application data. This is not an AI-generated report.\n...",
  "llm_provider": "Local evidence-based template (not AI)",
  "generated_at": "2026-11-22T22:50:33+00:00"
}
```
The legacy `llm_provider` response field contains the report-generator label for compatibility. A missing event returns `404`; report generation is local.

### `GET /api/reports`
List all generated intelligence reports.

### `GET /api/reports/{report_id}`
Retrieve a specific brief by report ID.

### `GET /api/reports/{report_id}/pdf`
Download the official generated PDF brief for a report.
