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

Open `.env` and configure your API keys as desired:

```ini
# Runtime Mode: 'demo' or 'live'
APP_MODE=demo

# Web Scraping Service: Firecrawl API Key (https://www.firecrawl.dev)
FIRECRAWL_API_KEY=

# Generative AI Provider Selection: 'openai' or 'gemini'
LLM_PROVIDER=openai

# LLM Provider Keys
OPENAI_API_KEY=
GEMINI_API_KEY=

# Memento Historical Memory Provider
MEMENTO_API_KEY=
MEMENTO_API_URL=https://api.memento.ai/v1

# Database URL (SQLite)
DATABASE_URL=sqlite:///./database/app.db

# Backend API Endpoint
API_BASE_URL=http://127.0.0.1:8000/api
```

> **Note on Zero-Configuration Demo Mode**:
> If you do not have external API keys yet, you can leave the keys blank. The system runs in fully functional **Demonstration Mode** using:
> - Realistic simulated web scraping of maritime and supply chain feeds
> - The Local Memento Development Adapter (`data/sample/memento_fallback.json`)
> - The deterministic 13-section Operational Brief synthesis engine

---

## 4. Database Initialization

Initialize the SQLite database schema and seed starter sources and incidents:
```bash
python -c "from database.db import init_db; init_db()"
```
This creates:
- `database/app.db` with all 6 tables (`disruptions`, `historical_events`, `operational_responses`, `sources`, `reports`, `collection_logs`).

---

## 5. Running the Application

### 5.1 Start the FastAPI Backend Server
In your first terminal window:
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify the backend is live:
```bash
curl http://127.0.0.1:8000/api/health
# Output: {"status":"ok","service":"LogisticsUpdate AI Backend","version":"1.0.0"}
```
Interactive OpenAPI documentation will be accessible at:
- `http://127.0.0.1:8000/docs`

### 5.2 Start the Streamlit Operations Command Center
In a second terminal window:
```bash
source .venv/bin/activate
streamlit run app/frontend.py
```
Open your browser to:
- `http://localhost:8501`

---

## 6. Running the Test Suite

Run all automated unit and integration tests:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```
All 21 test cases across the 6 test modules should pass:
- `tests/test_scraper.py`: Firecrawl collection & URL handling
- `tests/test_processing.py`: Pandas cleaning, deduplication, & severity logic
- `tests/test_history.py`: Memento storage, retrieval, & adapter status
- `tests/test_comparison.py`: TF-IDF cosine similarity & observation extraction
- `tests/test_llm.py`: 13-section brief synthesis & provenance guardrails
- `tests/test_pipeline.py`: Full end-to-end integration flow & PDF generation

---

## 7. Troubleshooting & FAQs

- **Port 8000 already in use?**
  Start FastAPI on another port: `uvicorn app.main:app --port 8080 --reload` and update `API_BASE_URL=http://127.0.0.1:8080/api` in your `.env`.
- **Database schema changes?**
  Delete `database/app.db` and re-run `python -c "from database.db import init_db; init_db()"`.
