"""PAGE 3: DATA COLLECTION
Orchestrates Firecrawl web-scraping agents across public maritime, rail,
and logistics port feeds. Includes source management and scraping audit logs.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post, api_delete):
    st.markdown('<div class="page-title">📡 Firecrawl Data Collection Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Configure target logistics feeds, execute scraping runs, and review audit ingestion logs.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🚀 Execute Ingestion Pipeline")
        st.info("Respects website access policies, extracts content, cleans text, normalizes dates, and assigns evidence-based severity.")

        if st.button("⚡ Run Full Scraping & Processing Pipeline", type="primary", use_container_width=True):
            with st.spinner("Executing Firecrawl scraper and Pandas processing pipeline..."):
                res = api_post("collect")
                if res and res.status_code == 200:
                    data = res.json()
                    st.success(
                        f"Pipeline Run Completed!\n\n"
                        f"• Sources Scraped: {data.get('sources_scraped', 0)}\n"
                        f"• Raw Articles Fetched: {data.get('fetched', 0)}\n"
                        f"• Cleaned Records: {data.get('processed', 0)}\n"
                        f"• Stored in DB & Memento: {data.get('stored', 0)}"
                    )
                    st.rerun()
                else:
                    st.error("Scraping execution encountered an error.")

        st.markdown("---")
        st.subheader("➕ Register New Monitoring Feed")
        with st.form("add_source_form"):
            s_name = st.text_input("Source Name", placeholder="e.g. Maritime Gateway News")
            s_url = st.text_input("Source Website URL", placeholder="https://maritime-feed.org/alerts")
            s_cat = st.selectbox(
                "Expected Category",
                [
                    "Port Disruption", "Weather Disruption", "Shipping Delay",
                    "Road Transportation Disruption", "Railway Disruption",
                    "Carrier Announcement", "Supply Chain Disruption", "Other"
                ]
            )
            submitted = st.form_submit_button("Add Monitoring Source")
            if submitted:
                if not s_name or not s_url:
                    st.error("Please supply both a name and a valid URL.")
                elif not s_url.startswith("http"):
                    st.error("URL must begin with http:// or https://")
                else:
                    res = api_post("sources", {"name": s_name, "url": s_url, "category": s_cat})
                    if res and res.status_code == 200:
                        st.success(f"Source '{s_name}' registered successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add source.")

    with col2:
        st.subheader("📋 Configured Public Feeds")
        sources = api_get("sources") or []
        if sources:
            for s in sources:
                with st.container():
                    c_a, c_b = st.columns([4, 1])
                    c_a.markdown(f"**{s.get('name')}** (`{s.get('category')}`)\n\n[{s.get('url')}]({s.get('url')})")
                    if c_b.button("Delete", key=f"del_src_{s.get('id')}"):
                        api_delete(f"sources/{s.get('id')}")
                        st.rerun()
                    st.markdown("<hr style='margin: 8px 0; border-color: #334155;'/>", unsafe_allow_html=True)
        else:
            st.info("No sources registered. Add one using the form.")

    st.markdown("---")
    st.subheader("📜 Scraping & Ingestion Audit Logs")
    logs = api_get("logs?limit=15") or []
    if logs:
        df_logs = pd.DataFrame(logs)[["created_at", "source_url", "status", "records_count", "error_message"]]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.caption("No historical collection logs available.")
