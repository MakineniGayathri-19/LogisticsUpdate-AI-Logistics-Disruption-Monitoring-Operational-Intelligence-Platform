# LogisticsUpdate AI – User Guide & Quickstart

## 1. Quickstart (Local Launch)

### Prerequisites
- macOS / Linux with Python 3.10+ (Python 3.13 supported)
- Virtual environment with dependencies installed

### Launching the Backend API
In your terminal, activate the virtual environment and start Uvicorn:
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will run on `http://127.0.0.1:8000`. You can test it in another tab:
```bash
curl http://127.0.0.1:8000/api/health
# Returns: {"status": "ok"}
```

### Launching the Streamlit Operations Dashboard
In a second terminal, activate the environment and launch Streamlit:
```bash
source .venv/bin/activate
streamlit run app/frontend.py
```
Open your browser to `http://localhost:8501`.

---

## 2. Navigating the 7 Dashboard Modules

1. **📊 Overview**: View total disruptions, critical alerts, monitored feeds, and severity distribution charts.
2. **⚡ Live Disruptions**: Filter active alerts by severity, category, or search keywords. Click **Generate AI Operational Brief** on any event to synthesize insights immediately.
3. **📡 Data Collection**: Click **Run Live Scraping & Processing** to ingest live feeds. Add or delete monitored feed URLs on demand.
4. **📜 Historical Events**: Browse Memento historical precedents with recorded operational responses and mitigation outcomes.
5. **🔍 Similarity & Comparison**: Choose any active disruption to run TF-IDF cosine similarity calculations against past precedents.
6. **🤖 AI Operational Reports**: Read formatted, strict no-hallucination operational briefs. Click **Download Brief (.txt)** to export for stakeholders.
7. **⚙️ Settings & Health**: Check API key configurations (OpenAI, Firecrawl) and re-initialize database tables if needed.

---

## 3. Environment Variables (`.env`)
Create a `.env` file from `.env.example`:
```env
FIRECRAWL_API_KEY="your-firecrawl-key"  # Optional: Runs demo scraper if blank
OPENAI_API_KEY="your-openai-key"        # Optional: Runs high-fidelity fallback if blank
DATABASE_URL="sqlite:///database/app.db"
APP_MODE="demo"
```
