# LogisticsUpdate AI 🚢⚡
### AI-Powered Logistics Disruption Monitoring & Operational Intelligence Platform

LogisticsUpdate AI is an end-to-end operational intelligence platform designed for logistics and supply chain command centers. The application monitors global public logistics sources, performs evidence-based data cleaning and severity scoring, retrieves historical precedents via Memento, benchmarks incidents with TF-IDF semantic comparison, and uses Generative AI to generate structured 13-section operational briefs with PDF export.

---

## 👥 College Project Team – Module Ownership

This project is built collaboratively by a team of four members:

| Team Member | Module & Responsibility | Technologies | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Member 1** | **Data Collection (Firecrawl)** | Python, Firecrawl SDK, Requests | Public web scraping, source feed management, raw payload storage (`data/raw/`), collection error handling, rate-limit resilience. |
| **Member 2** | **Data Processing & Cleaning** | Python, Pandas, Regex | Empty record pruning, duplicate elimination, category classification (8 classes), evidence-based severity rules, location extraction, processed datasets (`data/processed/`). |
| **Member 3** | **Historical Context & Comparison** | Memento API, Scikit-learn, TF-IDF | Dedicated Memento service adapter, historical precedent repository, operational response tracking, TF-IDF cosine similarity scoring. |
| **Member 4** | **Generative AI & Frontend Command Center** | OpenAI / Gemini, Streamlit, ReportLab | Prompt engineering, strict 13-section no-hallucination operational briefs, 7-page Streamlit dashboard, PDF export engine. |

---

## 🌟 Core Architecture & System Features

1. **⚡ Fast REST Backend**: FastAPI modular architecture with typed Pydantic schemas, CORS support, and interactive Swagger docs (`/docs`).
2. **🗄️ Relational Persistence**: SQLite + SQLAlchemy managing 6 distinct tables:
   - `disruptions` (live incoming alerts)
   - `historical_events` (ground-truth precedent repository)
   - `operational_responses` (actions taken and business outcomes)
   - `sources` (registered monitoring websites)
   - `reports` (generated AI intelligence briefs)
   - `collection_logs` (auditable scraping run logs)
3. **🕷️ Firecrawl Scraping Engine**: Extracts titles, published dates, and markdown content from maritime, port, and rail feeds.
4. **🏛️ Memento Historical Adapter**: Connects to Memento Cloud API or falls back gracefully to a verified Local Development Adapter with zero false claims.
5. **🔍 TF-IDF Semantic Precedent Matching**: Calculates incident similarity percentages and extracts common factors, key differences, and operational lessons.
6. **🤖 Strict 13-Section AI Operational Briefs**: Formatted briefs adhering to:
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
7. **📄 Official PDF Brief Export**: Integrated ReportLab export allowing instant download of operational briefs.
8. **🖥️ Modern 7-Page Streamlit Dashboard**: Dark navy and blue theme with responsive metric cards, interactive charts, and live filters.

---

## 📂 Project Directory Structure

```
LogisticsUpdate-AI/
├── app/
│   ├── main.py                     # FastAPI backend application entrypoint
│   ├── frontend.py                 # Streamlit master command center
│   └── pages/                      # Modular dashboard pages
│       ├── overview.py             # Page 1: High-level KPI metrics & charts
│       ├── live_disruptions.py     # Page 2: Live disruption stream & filters
│       ├── data_collection.py      # Page 3: Firecrawl scraping & source management
│       ├── historical_events.py    # Page 4: Memento precedent repository
│       ├── event_comparison.py     # Page 5: TF-IDF similarity comparison
│       ├── ai_reports.py           # Page 6: 13-section AI briefs & PDF download
│       └── settings.py             # Page 7: System configuration & diagnostics
├── backend/
│   ├── api/
│   │   └── routes.py               # FastAPI endpoints & Pydantic schemas
│   └── services/
│       ├── firecrawl_service.py    # Member 1: Web scraping & raw capture
│       ├── data_processing.py      # Member 2: Pandas cleaning & severity rules
│       ├── memento_manager.py      # Member 3: Memento adapter & response memory
│       ├── event_comparison.py     # Member 3: TF-IDF & cosine comparison engine
│       ├── llm_service.py          # Member 4: GenAI brief synthesis (OpenAI/Gemini)
│       ├── report_service.py       # Member 4: Report orchestration & ReportLab PDF
│       └── collect_service.py      # Master ingestion pipeline coordinator
├── database/
│   ├── db.py                       # SQLAlchemy engine & session setup
│   ├── models.py                   # 6 Table definitions
│   └── repositories.py             # Typed database CRUD & KPI queries
├── data/
│   ├── raw/                        # Raw scraped JSON files
│   ├── processed/                  # Cleaned CSV and JSON outputs
│   └── sample/                     # Memento fallback precedent records
├── utils/
│   ├── config.py                   # Dataclass settings & masked key utilities
│   ├── logger.py                   # Application logging
│   └── validators.py               # URL, schema, and category validators
├── tests/
│   ├── test_scraper.py             # Member 1 tests
│   ├── test_processing.py          # Member 2 tests
│   ├── test_history.py             # Member 3 tests
│   ├── test_comparison.py          # Member 3 comparison tests
│   ├── test_llm.py                 # Member 4 GenAI tests
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
*(Optional: Provide `FIRECRAWL_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`. If left blank, the app functions smoothly in full Demonstration Mode).*

### 3. Initialize Database
```bash
python -c "from database.db import init_db; init_db()"
```

### 4. Launch Backend API (Terminal 1)
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: `http://127.0.0.1:8000/docs`

### 5. Launch Streamlit Operations Center (Terminal 2)
```bash
source .venv/bin/activate
streamlit run app/frontend.py
```
Open your browser at: `http://localhost:8501`

---

## 🧪 Testing

Execute the automated test suite with full verbose reporting:
```bash
PYTHONPATH=. pytest tests/ -v
```
All 21 test cases validate:
- Firecrawl scraper URL handling & batch capture
- Pandas missing value pruning, deduplication, and severity heuristics
- Memento precedent persistence and response queries
- TF-IDF similarity calculation and variance extraction
- 13-section AI operational brief compliance and PDF generation

---

## 📊 Final Project Presentation Outline

For college evaluation and project demonstrations:

1. **Slide 1: Title & Team**: Introduction to LogisticsUpdate AI and the 4 member roles.
2. **Slide 2: Problem Statement**: Global supply chain volatility, maritime bottlenecks, and the need for precedent-backed operational intelligence.
3. **Slide 3: System Architecture**: End-to-end pipeline (Firecrawl -> Pandas -> SQLite -> Memento -> TF-IDF -> GenAI -> Streamlit).
4. **Slide 4: Live Demonstration**:
   - Ingesting a disruption feed (Data Collection page).
   - Exploring live alerts & rule-based severity (Live Disruptions).
   - Matching against historical precedents with TF-IDF similarity (Event Comparison).
   - Synthesizing a 13-section AI operational brief and downloading the official PDF (AI Reports).
5. **Slide 5: Innovation & Guardrails**:
   - Evidence-based severity rules prevent speculative ratings.
   - Grounded LLM synthesis strictly citing source URLs and Memento memory.
   - Dual-mode architecture (Live API integration + resilient zero-credential Demo Mode).
6. **Slide 6: Conclusion & Next Steps**: Live AIS telemetry integration, multi-modal container tracking, and ERP webhooks.
