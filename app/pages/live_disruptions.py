"""PAGE 2: LIVE DISRUPTIONS
Real-time disruption feeds with multi-criteria filtering, sorting,
detailed card/table inspection, and instant AI brief synthesis.
"""
import streamlit as st
import pandas as pd
from utils.config import settings
from utils.validators import is_valid_url

def render(api_get, api_post):
    st.markdown('<div class="page-title">⚡ Live Logistics Disruptions Stream</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time public disruption alerts harvested across global maritime, rail, and transit hubs.</div>', unsafe_allow_html=True)
    if not settings.is_firecrawl_active:
        st.info(
            "Demo mode: FIRECRAWL_API_KEY is not configured, so collection creates example updates "
            "instead of fetching live website content."
        )

    # Top Trigger & Actions Bar
    _, col_act = st.columns([3, 1])
    with col_act:
        if st.button("🔄 Trigger Live Collection", use_container_width=True, type="primary"):
            with st.spinner("Scraping sources and running data processing pipeline..."):
                res = api_post("collect")
                if res is None:
                    st.error("Could not reach the backend. Check the API connection and try again.")
                elif res.ok:
                    result = res.json()
                    if result.get("status") == "success":
                        st.success(f"Pipeline completed. Stored {result.get('stored', 0)} records.")
                    else:
                        st.warning(result.get("message", "The collection completed without new records."))
                else:
                    st.error(f"Collection failed (HTTP {res.status_code}): {res.text[:300]}")

    disruptions = api_get("disruptions") or []

    # Multi-factor Filters
    st.markdown("#### 🔎 Filter & Search Operations")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        cat_filter = st.selectbox(
            "Category",
            ["All", "Port Disruption", "Weather Disruption", "Shipping Delay",
             "Road Transportation Disruption", "Railway Disruption", "Carrier Announcement",
             "Supply Chain Disruption", "Other"]
        )
    with f_col2:
        sev_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low", "Unknown"])
    with f_col3:
        search_query = st.text_input("Search Title or Keywords", placeholder="e.g. Rotterdam, rail, flood...")
    with f_col4:
        sort_by = st.selectbox("Sort Order", ["Latest Arrived", "Highest Severity"])

    # Filtering Logic
    filtered = list(disruptions)
    if cat_filter != "All":
        filtered = [d for d in filtered if cat_filter.lower() in str(d.get("category", "")).lower()]
    if sev_filter != "All":
        filtered = [d for d in filtered if str(d.get("severity", "")).capitalize() == sev_filter]
    if search_query:
        q = search_query.lower()
        filtered = [
            d for d in filtered
            if q in str(d.get("title", "")).lower()
            or q in str(d.get("description", "")).lower()
            or q in str(d.get("location", "")).lower()
        ]

    # Sort
    if sort_by == "Highest Severity":
        sev_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Unknown": 0}
        filtered.sort(key=lambda x: sev_order.get(str(x.get("severity")).capitalize(), 0), reverse=True)

    st.caption(f"Displaying **{len(filtered)}** disruption records (out of {len(disruptions)} total)")

    view_mode = st.radio("Display Format", ["Detailed Card View", "Tabular Grid View"], horizontal=True)

    if view_mode == "Tabular Grid View":
        if filtered:
            df = pd.DataFrame(filtered)
            cols = [c for c in ["severity", "category", "title", "location", "source_name", "collected_at"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No disruptions match current filter criteria.")
    else:
        # Card View
        if not filtered:
            st.info("No disruptions match the selected filters.")
        for item in filtered:
            sev = item.get("severity", "Unknown")
            is_demo = bool(item.get("is_demo")) or (
                not settings.is_firecrawl_active
                and str(item.get("title", "")).startswith("Operational Disruption Update from ")
            )
            source_url = item.get("source_url", "")

            with st.container(border=True):
                demo_label = " · DEMO DATA" if is_demo else ""
                st.markdown(f"**{sev.upper()} · {item.get('category', 'Other')}{demo_label}**")
                st.subheader(item.get("title") or "Untitled disruption")
                st.write(item.get("description") or "No description available.")

                meta_col, source_col = st.columns([3, 1])
                with meta_col:
                    st.caption(
                        f"📍 {item.get('location') or 'Global / Unspecified'}"
                        f"  ·  📰 {item.get('source_name') or 'Unknown source'}"
                        f"  ·  🕒 {str(item.get('collected_at') or 'Unknown')[:19]}"
                    )
                with source_col:
                    if is_valid_url(source_url):
                        st.link_button("Open source", source_url, use_container_width=True)
                    else:
                        st.caption("Source link unavailable")

                if st.button("🤖 Generate AI Brief", key=f"gen_{item.get('id')}", type="primary"):
                    with st.spinner("Synthesizing 13-section operational brief..."):
                        res = api_post("reports/generate", {"event_id": item.get("id")})
                    if res and res.ok:
                        st.session_state["latest_report"] = res.json()
                        st.success("Brief generated. Open **AI Operational Reports** to view and download it.")
                    elif res:
                        st.error(f"Brief generation failed (HTTP {res.status_code}): {res.text[:300]}")
                    else:
                        st.error("Could not reach the backend. Check the API connection and try again.")
