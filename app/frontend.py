"""Streamlit Master Frontend for LogisticsUpdate AI.
Theme: Dark Navy & Blue Professional Command Center.
Routes cleanly to modular pages in app/pages/.
"""
import os
import streamlit as st
import requests

from app.pages import (
    overview,
    live_disruptions,
    data_collection,
    historical_events,
    event_comparison,
    ai_reports,
    settings as app_settings
)

# ---------------------------------------------------------------------------
# Streamlit Page Setup & Custom CSS Styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="LogisticsUpdate AI | Intelligence Platform",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional light operations dashboard theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F3F6FB;
        color: #172033;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color-scheme: light;
    }
    [data-testid="stMain"] {
        background:
            radial-gradient(ellipse at top right, rgba(37, 99, 235, 0.07), transparent 38%),
            #F3F6FB;
    }
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.94);
        border-bottom: 1px solid #E5EAF2;
    }
    [data-testid="stMain"] .block-container {
        max-width: 1440px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E5EAF2;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #475569;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin-bottom: 0.25rem;
    }
    .st-key-sidebar-navigation {
        gap: 0.25rem !important;
    }
    .st-key-sidebar-navigation [data-testid="stElementContainer"] {
        padding: 0 !important;
    }
    .st-key-sidebar-navigation [data-testid="stButton"] {
        margin-bottom: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0.55rem 0.75rem !important;
        min-height: 2.55rem !important;
        border-radius: 11px !important;
        box-shadow: none !important;
        transform: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button > div {
        width: 100%;
        justify-content: flex-start !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        color: #334155 !important;
        background: transparent !important;
        border-color: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        color: #1D4ED8 !important;
        background: #F1F5F9 !important;
        border-color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        color: #1D4ED8 !important;
        background: #EAF2FF !important;
        border-color: #BFDBFE !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] * {
        color: #1D4ED8 !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
        background: #DBEAFE !important;
        border-color: #93C5FD !important;
    }
    .page-title {
        font-size: clamp(1.45rem, 3vw, 2rem);
        font-weight: 800;
        color: #14213D;
        margin-bottom: 4px;
        letter-spacing: -0.6px;
    }
    .page-subtitle {
        font-size: 0.98rem;
        color: #64748B;
        margin-bottom: 1.25rem;
        line-height: 1.6;
        max-width: 900px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 750 !important;
        color: #2563EB !important;
    }
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 6px 20px rgba(20, 33, 61, 0.05);
        min-height: 112px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.86rem !important;
        color: #64748B !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricLabel"] * {
        color: #64748B !important;
        opacity: 1 !important;
    }
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] * {
        color: #334155 !important;
        opacity: 1 !important;
    }
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button {
        min-height: 2.7rem;
        border-radius: 11px;
        font-weight: 600;
        border: 1px solid #D7DFEA;
        transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
    }
    [data-testid="stBaseButton-secondary"],
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border-color: #D7DFEA !important;
    }
    [data-testid="stBaseButton-secondary"] *,
    button[kind="secondary"] * {
        color: inherit !important;
    }
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        color: #FFFFFF !important;
        border-color: #2563EB !important;
    }
    [data-testid="stBaseButton-primary"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);
        border-color: #93C5FD;
        box-shadow: 0 7px 18px rgba(37, 99, 235, 0.12);
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
    }
    [data-testid="stBaseButton-secondary"]:hover,
    button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
    }
    [data-testid="stButton"] button:focus-visible,
    [data-testid="stFormSubmitButton"] button:focus-visible {
        outline: 2px solid #60A5FA;
        outline-offset: 2px;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        color: #475569;
    }
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        background: #FFFFFF;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E2E8F0 !important;
        border-radius: 16px !important;
        background: #FFFFFF;
        box-shadow: 0 6px 20px rgba(20, 33, 61, 0.045);
    }
    [data-testid="stSelectbox"] [role="group"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] input,
    input:not([type="radio"]):not([type="checkbox"]),
    textarea {
        background-color: #FFFFFF !important;
        color: #172033 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }
    input[type="radio"],
    input[type="checkbox"] {
        accent-color: #2563EB !important;
    }
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
    }
    @media (max-width: 640px) {
        .st-key-dashboard-kpis [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }
        .st-key-dashboard-kpis [data-testid="stColumn"] {
            flex: 1 1 calc(33.333% - 0.75rem) !important;
            min-width: calc(33.333% - 0.75rem) !important;
            width: calc(33.333% - 0.75rem) !important;
        }
        .st-key-dashboard-kpis [data-testid="stMetric"] {
            min-height: 96px;
            padding: 0.75rem;
        }
        .st-key-dashboard-kpis [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
        }
    }
    @media (max-width: 420px) {
        .st-key-dashboard-kpis [data-testid="stColumn"] {
            flex-basis: calc(50% - 0.75rem) !important;
            min-width: calc(50% - 0.75rem) !important;
            width: calc(50% - 0.75rem) !important;
        }
    }
    hr {
        border-color: #E2E8F0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")

# Automatically launch backend in background if not already active
def _ensure_backend_running():
    try:
        res = requests.get(f"{API_BASE}/health", timeout=1.5)
        if res.status_code == 200:
            return
    except Exception:
        pass

    try:
        import threading
        import time
        import uvicorn
        from app.main import app as fastapi_app
        def run_uvicorn():
            uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
        t = threading.Thread(target=run_uvicorn, daemon=True)
        t.start()
        time.sleep(1.5)
    except Exception:
        pass

_ensure_backend_running()

# ---------------------------------------------------------------------------
# API Query Helpers
# ---------------------------------------------------------------------------

def api_get(endpoint: str):
    try:
        res = requests.get(f"{API_BASE}/{endpoint}", timeout=12)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

def api_post(endpoint: str, data: dict = None):
    try:
        res = requests.post(f"{API_BASE}/{endpoint}", json=data or {}, timeout=45)
        return res
    except Exception:
        return None

def api_delete(endpoint: str):
    try:
        return requests.delete(f"{API_BASE}/{endpoint}", timeout=10)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Sidebar Command Center
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="padding: 8px 0 14px 0;">
        <h2 style="color: #1D4ED8; margin: 0; font-size: 1.1rem;">🚢 Logistics AI</h2>
        <div style="color: #64748B; font-size: 0.78rem; margin-top: 4px; line-height: 1.45;">
            Disruption monitoring & operations intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

pages = [
    ("📊 Overview", "📊 Overview"),
    ("⚡ Live Disruptions", "⚡ Live Disruptions"),
    ("📡 Data Collection", "📡 Data Collection"),
    ("📜 Historical Events", "📜 Historical Events"),
    ("🔍 Event Comparison", "🔍 Event Comparison"),
    ("🤖 AI Operational Reports", "🤖 AI Reports"),
    ("⚙️ Settings & Diagnostics", "⚙️ Settings"),
]

page_keys = {page_key for page_key, _ in pages}
if st.session_state.get("selected_page") not in page_keys:
    st.session_state["selected_page"] = pages[0][0]

with st.sidebar.container(key="sidebar-navigation"):
    st.caption("WORKSPACE")
    for index, (page_key, label) in enumerate(pages):
        is_selected = st.session_state["selected_page"] == page_key
        if st.button(
            label,
            key=f"sidebar_nav_{index}",
            type="primary" if is_selected else "secondary",
            use_container_width=True,
        ):
            st.session_state["selected_page"] = page_key
            st.rerun()

selected_page = st.session_state["selected_page"]
st.sidebar.markdown("---")

# Backend Health Status Badge
health = api_get("health")
if health and health.get("status") == "ok":
    st.sidebar.markdown("🟢 **Backend API:** Online (`:8000`)")
else:
    st.sidebar.markdown("🔴 **Backend API:** Offline")
    st.sidebar.info("Start backend in terminal:\n`uvicorn app.main:app --reload`")

st.sidebar.markdown("---")
st.sidebar.caption("LogisticsUpdate AI v1.0.0\nCollege Team of 4 Project")

# ---------------------------------------------------------------------------
# Page Routing
# ---------------------------------------------------------------------------

if selected_page == "📊 Overview":
    overview.render(api_get, api_post)

elif selected_page == "⚡ Live Disruptions":
    live_disruptions.render(api_get, api_post)

elif selected_page == "📡 Data Collection":
    data_collection.render(api_get, api_post, api_delete)

elif selected_page == "📜 Historical Events":
    historical_events.render(api_get, api_post)

elif selected_page == "🔍 Event Comparison":
    event_comparison.render(api_get, api_post)

elif selected_page == "🤖 AI Operational Reports":
    ai_reports.render(api_get, api_post)

elif selected_page == "⚙️ Settings & Diagnostics":
    app_settings.render(api_get, api_post)
