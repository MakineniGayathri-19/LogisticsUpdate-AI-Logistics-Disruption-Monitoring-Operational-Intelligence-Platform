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
Returns connection status and adapter type for Memento memory.
```json
{
  "status": "local_fallback",
  "adapter": "Local Memento Adapter [Demo/Dev Mode]",
  "endpoint": ".../data/sample/memento_fallback.json",
  "is_live": false
}
```

---

## 2. Ingestion & Collection

### `POST /api/collect`
Triggers the full Firecrawl scraping, Pandas cleaning, categorization, and Memento storage pipeline.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "sources_scraped": 5,
  "fetched": 5,
  "processed": 5,
  "stored": 4,
  "errors_count": 0
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
Commit a historical event into the Memento memory repository.

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

## 6. AI Operational Reports

### `POST /api/reports/generate`
Synthesizes a 13-section Operational Intelligence Brief.
- **Payload**: `{"event_id": "<disruption_id>"}`
- **Response `200 OK`**:
```json
{
  "id": "a4b8e2d93e11",
  "disruption_id": "demo-dis-001",
  "content": "================================================================================\nLOGISTICSUPDATE AI – OPERATIONAL INTELLIGENCE BRIEF\n...",
  "llm_provider": "Deterministic Fallback [Demo Mode]",
  "generated_at": "2026-11-22T22:50:33+00:00"
}
```

### `GET /api/reports`
List all generated intelligence reports.

### `GET /api/reports/{report_id}`
Retrieve a specific brief by report ID.

### `GET /api/reports/{report_id}/pdf`
Download the official generated PDF brief for a report.
