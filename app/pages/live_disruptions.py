"""PAGE 2: LIVE DISRUPTIONS
Real-time disruption feeds with multi-criteria filtering, sorting,
detailed card/table inspection, and instant AI brief synthesis.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post):
    st.markdown('<div class="page-title">⚡ Live Logistics Disruptions Stream</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time public disruption alerts harvested across global maritime, rail, and transit hubs.</div>', unsafe_allow_html=True)

    # Top Trigger & Actions Bar
    col_act1, col_act2 = st.columns([3, 1])
    with col_act2:
        if st.button("🔄 Trigger Live Collection", use_container_width=True, type="primary"):
            with st.spinner("Scraping sources and running data processing pipeline..."):
                res = api_post("collect")
                if res and res.status_code == 200:
                    st.success(f"Pipeline executed! Ingested {res.json().get('stored', 0)} new records.")
                    st.rerun()
                else:
                    st.warning("Collection triggered (running in demo mode if keys unset).")

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

    st.caption(f"Displaying **{len(filtered)}** active disruption records (out of {len(disruptions)} total)")

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
            badge_color = "#DC2626" if sev == "Critical" else "#EA580C" if sev == "High" else "#D97706" if sev == "Medium" else "#2563EB"
            is_demo = item.get("is_demo", False)

            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #0F172A; border: 1px solid #334155; border-left: 5px solid {badge_color}; padding: 16px; border-radius: 8px; margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="background-color: {badge_color}; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{sev.upper()}</span>
                                <span style="background-color: #1E293B; color: #94A3B8; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; margin-left: 6px;">{item.get('category')}</span>
                                {'<span style="background-color: #374151; color: #FBBF24; padding: 3px 6px; border-radius: 4px; font-size: 0.70rem; margin-left: 6px;">DEMO DATA</span>' if is_demo else ''}
                            </div>
                            <span style="color: #94A3B8; font-size: 0.8rem;">🕒 {item.get('collected_at', '')[:19]}</span>
                        </div>
                        <h4 style="color: #F8FAFC; margin-top: 10px; margin-bottom: 6px;">{item.get('title')}</h4>
                        <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.4;">{item.get('description')}</p>
                        <div style="display: flex; gap: 20px; font-size: 0.85rem; color: #94A3B8; margin-top: 10px;">
                            <span>📍 <b>Location:</b> {item.get('location') or 'Global / Unspecified'}</span>
                            <span>📰 <b>Source:</b> <a href="{item.get('source_url')}" target="_blank" style="color: #38BDF8;">{item.get('source_name')}</a></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2, c3 = st.columns([2, 1, 1])
                with c3:
                    if st.button("🤖 Generate AI Brief", key=f"gen_{item.get('id')}", use_container_width=True):
                        with st.spinner("Synthesizing 13-section operational brief..."):
                            res = api_post("reports/generate", {"event_id": item.get("id")})
                            if res and res.status_code == 200:
                                st.success("Intelligence brief synthesized! Navigate to **AI Operational Reports** to inspect.")
                            else:
                                st.error("Failed to generate brief.")
