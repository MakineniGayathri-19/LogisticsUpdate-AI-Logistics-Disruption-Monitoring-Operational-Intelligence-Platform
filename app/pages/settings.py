"""PAGE 7: SETTINGS & HEALTH
Application configuration, API status diagnostics, masked keys,
database maintenance, and College Project Team ownership attribution.
"""
import streamlit as st
import pandas as pd
from utils.config import settings

def render(api_get, api_post):
    st.markdown('<div class="page-title">⚙️ System Configuration & Diagnostics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Inspect API connection states, credentials posture, database tables, and team ownership.</div>', unsafe_allow_html=True)

    # Backend Connection
    health = api_get("health")
    if health and health.get("status") == "ok":
        st.success("🟢 **Backend Core API:** Online and responding (HTTP 200)")
    else:
        st.error("🔴 **Backend Core API:** Unreachable. Ensure FastAPI is running on port 8000.")

    st.markdown("---")

    # API Services Status Grid
    st.subheader("🔌 External Integration Status")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 📡 Firecrawl Web Scraper")
        if settings.is_firecrawl_active:
            st.success(f"🟢 **Firecrawl API:** Active (Key: `{settings.mask_key(settings.firecrawl_api_key)}`)")
        else:
            st.warning("🟡 **Firecrawl API:** Demo Mode Active (Simulated Scraper Fallback)")
            st.caption("To activate live scraping, set `FIRECRAWL_API_KEY` in your `.env` file.")

        st.markdown("#### 🧠 Generative AI Engine")
        provider = settings.llm_provider
        if provider == "openai":
            if settings.openai_api_key:
                st.success(f"🟢 **OpenAI LLM:** Configured (Key: `{settings.mask_key(settings.openai_api_key)}`)")
            else:
                st.warning("🟡 **OpenAI LLM:** Demo Fallback Mode (Deterministic 13-Section Brief Generator)")
        elif provider == "gemini":
            if settings.gemini_api_key:
                st.success(f"🟢 **Google Gemini LLM:** Configured (Key: `{settings.mask_key(settings.gemini_api_key)}`)")
            else:
                st.warning("🟡 **Google Gemini LLM:** Demo Fallback Mode (Deterministic 13-Section Brief Generator)")

    with c2:
        st.markdown("#### 🏛️ Memento Historical Context")
        m_stat = api_get("memento/status") or {}
        if m_stat.get("is_live"):
            st.success(f"🟢 **Memento:** Cloud Connected (`{m_stat.get('endpoint')}`)")
        else:
            st.info(f"🏛️ **Memento:** {m_stat.get('adapter', 'Local Memento Adapter [Demo/Dev Mode]')}")
            st.caption(f"Storage: `{m_stat.get('endpoint')}`")

        st.markdown("#### 🗄️ Database & Storage")
        st.markdown(f"**Database URL:** `{settings.database_url}`")
        st.markdown(f"**Application Mode:** `{settings.mode.upper()}`")

    st.markdown("---")

    # Database Maintenance
    st.subheader("🛠️ Database Maintenance & Seeding")
    col_db1, col_db2 = st.columns(2)
    with col_db1:
        if st.button("🔄 Re-initialize Database Tables", use_container_width=True):
            from database.db import init_db
            init_db()
            st.success("Database tables refreshed and sample data re-seeded.")
            st.rerun()

    st.markdown("---")

    # Team Ownership Matrix
    st.subheader("👥 College Project Team – Module Ownership")
    team_data = [
        {
            "Member": "Member 1",
            "Module": "Data Collection (Firecrawl)",
            "Key Deliverables": "Firecrawl SDK, Website Source Management, Public Scraping Pipeline, Raw JSON Storage, Rate Limit Handling"
        },
        {
            "Member": "Member 2",
            "Module": "Data Processing & Cleaning",
            "Key Deliverables": "Pandas Pipeline, Duplicate Elimination, Categorization (8 Classes), Evidence-based Severity Rules, Cleaned Datasets"
        },
        {
            "Member": "Member 3",
            "Module": "Historical Memory (Memento)",
            "Key Deliverables": "Memento Service Adapter, Historical Precedent Storage, Response/Outcome Tracking, TF-IDF Cosine Similarity Engine"
        },
        {
            "Member": "Member 4",
            "Module": "LLM Synthesis & Frontend",
            "Key Deliverables": "Configurable LLM (OpenAI/Gemini), 13-Section Operational Brief, Streamlit 7-Page Dashboard, PDF Export"
        }
    ]
    st.table(pd.DataFrame(team_data))
