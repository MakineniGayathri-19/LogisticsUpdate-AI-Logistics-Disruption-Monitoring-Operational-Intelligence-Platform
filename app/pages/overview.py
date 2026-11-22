"""PAGE 1: OVERVIEW DASHBOARD
Displays high-level logistics intelligence KPIs, interactive charts,
priority alerts, and ingestion status using real application data.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post):
    st.markdown('<div class="page-title">🌐 Global Logistics Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time situational awareness, disruption velocity, and precedent analytics.</div>', unsafe_allow_html=True)

    collection_notice = st.session_state.pop("collection_notice", None)
    if collection_notice:
        st.success(collection_notice)

    action_refresh, action_collect = st.columns(2)
    with action_refresh:
        if st.button("↻ Refresh dashboard", use_container_width=True, key="overview_refresh"):
            st.rerun()
    with action_collect:
        if st.button("⚡ Collect latest updates", type="primary", use_container_width=True, key="overview_collect"):
            with st.spinner("Collecting and processing source updates..."):
                response = api_post("collect")
            if response is None:
                st.error("Could not reach the backend. Check the API connection and try again.")
            elif response.ok:
                result = response.json()
                if result.get("status") == "success":
                    st.session_state["collection_notice"] = (
                        f"Collection complete: {result.get('stored', 0)} records stored "
                        f"from {result.get('sources_scraped', 0)} sources."
                    )
                    st.rerun()
                else:
                    st.warning(result.get("message", "The collection completed without new records."))
            else:
                st.error(f"Collection failed (HTTP {response.status_code}): {response.text[:300]}")

    # Fetch live data from backend API
    stats = api_get("stats") or {}
    disruptions = api_get("disruptions") or []
    reports = api_get("reports") or []
    historical = api_get("historical-events") or []

    # KPI Metrics Row
    total_dis = stats.get("total_disruptions", len(disruptions))
    active_dis = stats.get("active_disruptions", sum(1 for d in disruptions if d.get("status") == "Active"))
    critical_dis = stats.get("critical_disruptions", sum(1 for d in disruptions if str(d.get("severity")).capitalize() == "Critical"))
    high_dis = stats.get("high_disruptions", sum(1 for d in disruptions if str(d.get("severity")).capitalize() == "High"))
    hist_count = stats.get("historical_stored", len(historical))
    rep_count = stats.get("ai_reports_generated", len(reports))
    last_col = stats.get("last_collection_time", "Active")

    with st.container(key="dashboard-kpis"):
        kpi_row1 = st.columns(3)
        with kpi_row1[0]:
            st.metric("Total Disruptions", total_dis)
        with kpi_row1[1]:
            st.metric("Active Events", active_dis, delta=f"{critical_dis} Critical", delta_color="inverse")
        with kpi_row1[2]:
            st.metric("Critical Alerts", critical_dis)

        kpi_row2 = st.columns(3)
        with kpi_row2[0]:
            st.metric("High Priority", high_dis)
        with kpi_row2[1]:
            st.metric("Historical Precedents", hist_count)
        with kpi_row2[2]:
            st.metric("AI Briefs Generated", rep_count)

    st.markdown("---")

    # Visual Analytics Grid (4 Charts)
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        with st.container(border=True):
            st.subheader("📊 Disruptions by Category")
            if disruptions:
                df_dis = pd.DataFrame(disruptions)
                cat_counts = df_dis["category"].value_counts()
                st.bar_chart(cat_counts, horizontal=True, height=280, color="#3B82F6")
            else:
                st.info("No disruption data available.")

    with col_chart2:
        with st.container(border=True):
            st.subheader("⚠️ Severity Distribution")
            if disruptions:
                df_dis = pd.DataFrame(disruptions)
                sev_counts = df_dis["severity"].value_counts()
                st.bar_chart(sev_counts, horizontal=True, height=260, color="#F59E0B")
            else:
                st.info("No disruption data available.")

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        with st.container(border=True):
            st.subheader("📍 Disruptions by Location Hub")
            if disruptions:
                df_dis = pd.DataFrame(disruptions)
                loc_series = df_dis["location"].fillna("Unspecified").value_counts().head(7)
                st.bar_chart(loc_series, horizontal=True, height=320, color="#10B981")
            else:
                st.info("No location data available.")

    with col_chart4:
        with st.container(border=True):
            st.subheader("🕒 Ingestion Velocity & Collection Audit")
            st.markdown(f"**Last Successful Collection Run:** `{last_col}`")
            logs = api_get("logs?limit=5") or []
            if logs:
                df_logs = pd.DataFrame(logs)[["source_url", "status", "records_count", "created_at"]]
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.caption("No recent collection logs recorded.")

    st.markdown("---")

    # Priority Disruption Highlights
    st.subheader("🚨 High-Priority Live Disruption Stream")
    high_priority = [d for d in disruptions if str(d.get("severity")).capitalize() in ("Critical", "High")]
    if high_priority:
        for item in high_priority[:4]:
            sev = item.get("severity", "Alert")
            with st.container(border=True):
                st.markdown(f"**{sev.upper()}** · {item.get('title')}")
                st.caption(
                    f"📍 {item.get('location') or 'Unspecified'}"
                    f"  ·  🏷️ {item.get('category')}"
                    f"  ·  📰 {item.get('source_name')}"
                )
    else:
        st.info("No critical or high-priority disruptions currently active.")
