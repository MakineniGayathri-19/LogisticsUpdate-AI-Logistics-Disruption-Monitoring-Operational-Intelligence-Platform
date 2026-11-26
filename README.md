# LogisticsUpdate AI 🚢⚡
### Logistics Disruption Monitoring & Operational Intelligence Platform

LogisticsUpdate AI is an end-to-end operational intelligence platform designed for logistics and supply chain command centers. It ingests source-backed public alerts, calculates a transparent 24-hour weather exposure index from live forecasts, compares incidents only against recorded historical events, and generates local 13-section operational reports from stored evidence. Reports require no external credentials and are not generative-AI output.

---

## 👥 College Project Team – Module Ownership

This project is built collaboratively by a team of four members:

| Team Member | Module & Responsibility | Technologies | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Member 1** | **Public Data Collection** | Python, Firecrawl SDK, Requests | NOAA alert collection, optional web scraping, raw payload storage (`data/raw/`), source feed management, and collection error handling. |
| **Member 2** | **Data Processing & Cleaning** | Python, Pandas, Regex | Empty record pruning, duplicate elimination, category classification (8 classes), evidence-based severity rules, location extraction, processed datasets (`data/processed/`). |
| **Member 3** | **Historical Context & Comparison** | SQLite, Scikit-learn, TF-IDF | Source-backed historical precedent repository, operational response tracking, TF-IDF cosine similarity scoring. |
| **Member 4** | **Operational Reports & Frontend Command Center** | FastAPI, HTML/CSS/JavaScript, ReportLab | Local evidence-based 13-section reports, responsive web dashboard, and PDF export engine. |

---

## 🌟 Core Architecture & System Features

1. **⚡ Fast REST Backend**: FastAPI modular architecture with typed Pydantic schemas, CORS support, and interactive Swagger docs (`/docs`).
2. **🗄️ Relational Persistence**: SQLite + SQLAlchemy managing 6 distinct tables:
   - `disruptions` (live incoming alerts)
   - `historical_events` (source-backed recorded precedent repository)
   - `operational_responses` (actions taken and business outcomes)
   - `sources` (registered monitoring websites)
   - `reports` (generated operational reports)
   - `collection_logs` (auditable scraping run logs)
3. **🕷️ Firecrawl Scraping Engine**: Extracts titles, published dates, and markdown content from maritime, port, and rail feeds.
4. **🌦️ Live Weather Forecast**: Retrieves the next 24 hours of Open-Meteo weather data for six logistics hubs and calculates a transparent weather-risk index. This index is not presented as a trained probability.
5. **🏛️ Source-backed Historical Memory**: Historical comparisons use only records stored with source references and documented outcomes; the store starts empty instead of including synthetic sample precedents.
6. **🔍 TF-IDF Semantic Precedent Matching**: Calculates incident similarity percentages and extracts common factors, key differences, and operational lessons.
7. **📋 Strict 13-Section Operational Reports**: Generated locally from stored event facts and historical records. They are template-based, not generative AI, and clearly identify missing evidence. Each report includes:
   1. Executive Summary
   2. Current Disruption Details
   3. Disruption Category
   4. Location
   5. Severity and Justification
   6. Potential Operational Impact
   7. Historical Event Comparison
   8. Previous Operational Responses
   9. Key Changes & Dynamics
   10. Recommended Monitoring Actions
   11. Operational Considerations & Contingencies
   12. Source References
   13. Data Limitations and Uncertainties
8. **📄 Official PDF Brief Export**: Integrated ReportLab export allowing instant download of operational briefs.
9. **🖥️ FastAPI Operations Dashboard**: Responsive command center served directly by FastAPI, with live analytics, operational workflows, and no separate frontend runtime.

---

## 📂 Project Directory Structure

```
LogisticsUpdate-AI/
├── app/
│   ├── main.py                     # FastAPI app, static dashboard, and API entrypoint
│   └── static/                     # Responsive HTML/CSS/JavaScript operations dashboard
├── backend/
│   ├── api/
│   │   └── routes.py               # FastAPI endpoints & Pydantic schemas
│   └── services/
│       ├── firecrawl_service.py    # Member 1: Web scraping & raw capture
│       ├── forecast_service.py     # Live Open-Meteo forecast and weather-risk index
│       ├── data_processing.py      # Member 2: Pandas cleaning & severity rules
│   ├── memento_manager.py          # Member 3: SQLite historical-event access
│       ├── event_comparison.py     # Member 3: TF-IDF & cosine comparison engine
│       ├── llm_service.py          # Member 4: Local evidence-based report generation
│       ├── report_service.py       # Member 4: Report orchestration & ReportLab PDF
│       └── collect_service.py      # Master ingestion pipeline coordinator
├── database/
│   ├── db.py                       # SQLAlchemy engine & session setup
│   ├── models.py                   # 6 Table definitions
│   └── repositories.py             # Typed database CRUD & KPI queries
├── data/
│   ├── raw/                        # Raw public API and scraped JSON files
│   ├── processed/                  # Cleaned data and forecast CSV/JSON outputs
├── utils/
│   ├── config.py                   # Dataclass settings & masked key utilities
│   ├── logger.py                   # Application logging
│   └── validators.py               # URL, schema, and category validators
├── tests/
│   ├── test_frontend.py            # FastAPI dashboard route and static asset tests
│   ├── test_scraper.py             # Live-source and Firecrawl behavior tests
│   ├── test_forecast.py            # Weather risk index and snapshot tests
│   ├── test_processing.py          # Member 2 tests
│   ├── test_history.py             # Source-backed historical record tests
│   ├── test_comparison.py          # Member 3 comparison tests
│   ├── test_llm.py                 # Local operational report tests
│   └── test_pipeline.py            # End-to-end integration tests
├── docs/
│   ├── architecture.md             # System architecture & data flow diagrams
│   ├── setup.md                    # Installation & environment guide
│   ├── user_guide.md               # Dashboard operations walkthrough
│   └── api.md                      # REST API endpoints & schemas
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Setup Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Operational reports do not need an API key. Add `FIRECRAWL_API_KEY` only if you want to scrape the configured public websites; NOAA severe alerts and Open-Meteo forecasts are available from public endpoints without a key.

### 3. Initialize Database
```bash
python -c "from database.db import init_db; init_db()"
```

### 4. Launch the FastAPI application
```bash
./run.sh
```
The script starts the server and opens the operations dashboard in your browser. API docs are available at `http://127.0.0.1:8000/docs`.

---

## 🧪 Testing

Execute the automated test suite with full verbose reporting:
```bash
PYTHONPATH=. pytest tests/ -v
```
The test suite validates:
- Firecrawl scraper URL handling & batch capture
- Pandas missing value pruning, deduplication, and severity heuristics
- Real historical record persistence and response queries
- Forecast score calculations and saved public-data snapshots
- TF-IDF similarity calculation and variance extraction
- 13-section local operational report generation and PDF export

---

## 📊 Final Project Presentation Outline

For college evaluation and project demonstrations:

1. **Slide 1: Title & Team**: Introduction to LogisticsUpdate AI and the 4 member roles.
2. **Slide 2: Problem Statement**: Global supply chain volatility, maritime bottlenecks, and the need for precedent-backed operational intelligence.
3. **Slide 3: System Architecture**: End-to-end pipeline (Firecrawl -> Pandas -> SQLite -> Memento -> TF-IDF -> GenAI -> FastAPI dashboard).
4. **Slide 4: Live Demonstration**:
   - Ingesting a disruption feed (Data Collection page).
   - Exploring live alerts & rule-based severity (Live Disruptions).
   - Matching against historical precedents with TF-IDF similarity (Event Comparison).
   - Generating a 13-section local operational report and downloading its PDF (Operational Reports).
5. **Slide 5: Innovation & Guardrails**:
   - Evidence-based severity rules prevent speculative ratings.
   - Reports are generated locally from recorded facts and explicitly identify their limitations.
   - Public source-backed feeds and no external AI/API-key requirement for reports.
6. **Slide 6: Conclusion & Next Steps**: Live AIS telemetry integration, multi-modal container tracking, and ERP webhooks.
