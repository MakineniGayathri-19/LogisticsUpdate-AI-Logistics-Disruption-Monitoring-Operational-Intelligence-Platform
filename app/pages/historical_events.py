"""PAGE 4: HISTORICAL EVENTS
Memento memory repository for archival logistics incidents, documented
operational responses, and real-world outcomes.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post):
    st.markdown('<div class="page-title">📜 Memento Historical Precedent Repository</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Preserves historical disruption precedents and past operational mitigation actions.</div>', unsafe_allow_html=True)

    # Status Banner
    memento_status = api_get("memento/status") or {}
    adapter_name = memento_status.get("adapter", "Local Memento Adapter [Demo/Dev Mode]")
    is_live = memento_status.get("is_live", False)

    if is_live:
        st.success(f"🟢 **Memento Service:** {adapter_name} (Cloud Connected)")
    else:
        st.info(f"🏛️ **Memento Service:** {adapter_name} — Operating on verified local incident baseline. (Clearly identified: Demo / Development Adapter)")

    # Fetch historical events
    historical_events = api_get("historical-events") or []

    # Search & Category Filters
    f1, f2 = st.columns(2)
    with f1:
        cat_filter = st.selectbox(
            "Filter Category",
            ["All", "Port Disruption", "Weather Disruption", "Shipping Delay",
             "Railway Disruption", "Road Transportation Disruption", "Supply Chain Disruption", "Other"]
        )
    with f2:
        search_kw = st.text_input("Filter by Location or Keyword", placeholder="e.g. Rotterdam, Chicago, drought...")

    filtered_events = list(historical_events)
    if cat_filter != "All":
        filtered_events = [e for e in filtered_events if cat_filter.lower() in str(e.get("category", "")).lower()]
    if search_kw:
        q = search_kw.lower()
        filtered_events = [
            e for e in filtered_events
            if q in str(e.get("title", "")).lower()
            or q in str(e.get("description", "")).lower()
            or q in str(e.get("location", "")).lower()
        ]

    st.caption(f"Showing **{len(filtered_events)}** historical precedents in memory")

    tab_browse, tab_add = st.tabs(["🏛️ Browse Historical Precedents", "➕ Add Precedent to Memory"])

    with tab_browse:
        for ev in filtered_events:
            sev = ev.get("severity", "High")
            with st.expander(f"📍 [{sev}] {ev.get('title')} ({ev.get('category')}) — {ev.get('location', 'Global')}"):
                st.markdown(f"**Disruption Description:**\n{ev.get('description')}")
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🛡️ Previous Operational Response Taken:**")
                    st.info(ev.get("response", "Standard modal rerouting protocol."))
                with c2:
                    st.markdown("**🎯 Historical Outcome Achieved:**")
                    st.success(ev.get("outcome", "Dwell time normalized within 72 hours."))
                st.caption(f"ID: {ev.get('id')} | Source: {ev.get('source_url', 'N/A')} | Origin: {'DEMO DATA' if ev.get('is_demo') else 'VERIFIED HISTORICAL'}")

    with tab_add:
        st.subheader("Record New Historical Incident & Operational Response")
        with st.form("manual_history_form"):
            h_title = st.text_input("Incident Title", placeholder="e.g. Port of Antwerp Crane Collapse")
            h_desc = st.text_area("Incident Description", placeholder="Details of how disruption unfolded...")
            c_a, c_b = st.columns(2)
            h_cat = c_a.selectbox("Category", [
                "Port Disruption", "Weather Disruption", "Shipping Delay",
                "Road Transportation Disruption", "Railway Disruption", "Carrier Announcement",
                "Supply Chain Disruption", "Other"
            ])
            h_loc = c_b.text_input("Location", placeholder="e.g. Antwerp, Belgium")
            h_sev = c_a.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
            h_src = c_b.text_input("Source Reference URL", placeholder="https://...")

            st.markdown("#### Operational Lessons")
            h_resp = st.text_area("Operational Response Enacted", placeholder="What specific action did operations take?")
            h_out = st.text_area("Operational Outcome Achieved", placeholder="What was the measurable outcome or resolution timeline?")

            submitted = st.form_submit_button("Save Precedent to Memento Store")
            if submitted:
                if not h_title or not h_desc:
                    st.error("Title and description are required.")
                else:
                    payload = {
                        "title": h_title,
                        "description": h_desc,
                        "category": h_cat,
                        "location": h_loc or "Unspecified",
                        "severity": h_sev,
                        "response": h_resp,
                        "outcome": h_out,
                        "source_name": "Manual Operations Input",
                        "source_url": h_src or "https://logisticsupdate.internal"
                    }
                    res = api_post("historical-events", payload)
                    if res and res.status_code == 200:
                        st.success("Precedent committed to Memento repository!")
                        st.rerun()
                    else:
                        st.error("Failed to commit historical event.")
