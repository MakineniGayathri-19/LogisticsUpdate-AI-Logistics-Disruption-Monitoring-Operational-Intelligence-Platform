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

# Professional Dark Navy & Blue Theme CSS
st.markdown(
    """
    <style>
    /* Dark Navy Theme Styling */
    .stApp {
        background-color: #0B132B;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }
    .page-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .page-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 22px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    hr {
        border-color: #1E293B !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

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
    <div style="padding: 10px 0 16px 0;">
        <h2 style="color: #38BDF8; margin: 0; font-size: 1.4rem;">🚢 LogisticsUpdate AI</h2>
        <div style="color: #94A3B8; font-size: 0.75rem; margin-top: 3px;">
            AI-Powered Logistics Disruption Monitoring & Operational Intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

pages = [
    "📊 Overview",
    "⚡ Live Disruptions",
    "📡 Data Collection",
    "📜 Historical Events",
    "🔍 Event Comparison",
    "🤖 AI Operational Reports",
    "⚙️ Settings & Diagnostics"
]

selected_page = st.sidebar.radio("Command Navigation", pages, index=0)
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
