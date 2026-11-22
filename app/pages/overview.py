"""PAGE 1: OVERVIEW DASHBOARD
Displays high-level logistics intelligence KPIs, interactive charts,
priority alerts, and ingestion status using real application data.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post):
    st.markdown('<div class="page-title">🌐 Global Logistics Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time situational awareness, disruption velocity, and precedent analytics.</div>', unsafe_allow_html=True)

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

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    with kpi1:
        st.metric("Total Disruptions", total_dis)
    with kpi2:
        st.metric("Active Events", active_dis, delta=f"{critical_dis} Critical", delta_color="inverse")
    with kpi3:
        st.metric("Critical Alerts", critical_dis)
    with kpi4:
        st.metric("High Priority", high_dis)
    with kpi5:
        st.metric("Historical Precedents", hist_count)
    with kpi6:
        st.metric("AI Briefs Generated", rep_count)

    st.markdown("---")

    # Visual Analytics Grid (4 Charts)
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Disruptions by Category")
        if disruptions:
            df_dis = pd.DataFrame(disruptions)
            cat_counts = df_dis["category"].value_counts()
            st.bar_chart(cat_counts, color="#3B82F6")
        else:
            st.info("No disruption data available.")

    with col_chart2:
        st.subheader("⚠️ Severity Distribution")
        if disruptions:
            df_dis = pd.DataFrame(disruptions)
            sev_counts = df_dis["severity"].value_counts()
            st.bar_chart(sev_counts, color="#F59E0B")
        else:
            st.info("No disruption data available.")

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("📍 Disruptions by Location Hub")
        if disruptions:
            df_dis = pd.DataFrame(disruptions)
            loc_series = df_dis["location"].fillna("Unspecified").value_counts().head(7)
            st.bar_chart(loc_series, color="#10B981")
        else:
            st.info("No location data available.")

    with col_chart4:
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
            badge_color = "#DC2626" if sev == "Critical" else "#EA580C"
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #1E293B; border-left: 4px solid {badge_color}; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px;">
                        <span style="background-color: {badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{sev.upper()}</span>
                        <strong style="margin-left: 8px; font-size: 1rem; color: #F8FAFC;">{item.get('title')}</strong>
                        <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                            📍 {item.get('location')} &nbsp;|&nbsp; 🏷️ {item.get('category')} &nbsp;|&nbsp; 📰 Source: {item.get('source_name')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No critical or high-priority disruptions currently active.")
