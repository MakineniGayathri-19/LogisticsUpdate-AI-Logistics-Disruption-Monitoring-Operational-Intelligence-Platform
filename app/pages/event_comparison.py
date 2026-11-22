"""PAGE 5: EVENT COMPARISON
Benchmarks active logistics disruptions against historical incidents
using TF-IDF feature extraction and Cosine Similarity scoring.
"""
import streamlit as st
import pandas as pd

def render(api_get, api_post):
    st.markdown('<div class="page-title">🔍 Historical Event Comparison Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">TF-IDF semantic vectorization, precedent similarity scores, and operational variance analysis.</div>', unsafe_allow_html=True)

    disruptions = api_get("disruptions") or []

    if not disruptions:
        st.warning("No active disruptions available in the system. Trigger a collection run first.")
        return

    # Selection Box
    options = {f"[{d.get('severity', 'Alert')}] {d.get('title')} ({d.get('location') or 'Global'})": d.get("id") for d in disruptions}
    selected_label = st.selectbox("Select Active Disruption to Compare with Historical Precedents:", list(options.keys()))
    selected_id = options[selected_label]

    current_event = next((d for d in disruptions if d.get("id") == selected_id), None)

    if current_event:
        with st.container(border=True):
            st.caption("CURRENT DISRUPTION BENCHMARK")
            st.subheader(current_event.get("title") or "Untitled disruption")
            st.write(current_event.get("description") or "No description available.")
            meta_category, meta_location, meta_severity = st.columns(3)
            meta_category.metric("Category", current_event.get("category") or "Other")
            meta_location.metric("Location", current_event.get("location") or "Unspecified")
            meta_severity.metric("Severity", current_event.get("severity") or "Unknown")

    if st.button("⚡ Compute Similarity & Analyze Precedents", type="primary", use_container_width=True):
        with st.spinner("Extracting TF-IDF n-grams and calculating cosine similarity..."):
            res = api_post(f"compare/{selected_id}")
            if res and res.status_code == 200:
                data = res.json()
                matches = data.get("similar_events", [])

                if not matches:
                    st.info("No matching historical incidents met the similarity threshold.")
                else:
                    st.success(f"Matched **{len(matches)}** relevant historical precedents in memory!")

                    for i, m in enumerate(matches, 1):
                        sim_pct = m.get("similarity_percentage", 0.0)
                        ev = m.get("event", {})

                        with st.container(border=True):
                            title_col, score_col = st.columns([3, 1])
                            with title_col:
                                st.subheader(f"#{i} Precedent: {m.get('title') or 'Untitled event'}")
                            with score_col:
                                st.metric("Similarity", f"{sim_pct:.1f}%")
                            st.progress(min(max(sim_pct / 100, 0), 1))
                            st.caption(
                                f"{m.get('category') or 'Other'}"
                                f"  ·  {m.get('location') or 'Unspecified'}"
                            )

                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown("##### 🛡️ Previous Operational Response Taken")
                                st.info(m.get("previous_response", "Standard rerouting."))
                            with c2:
                                st.markdown("##### 🎯 Historical Outcome Achieved")
                                st.success(m.get("historical_outcome", "Dwell time normalized."))

                            c_diff, c_obs = st.columns(2)
                            with c_diff:
                                st.markdown("##### ⚖️ Key Differences")
                                for diff in m.get("key_differences", []):
                                    st.markdown(f"• {diff}")
                            with c_obs:
                                st.markdown("##### 💡 Important Operational Observations")
                                for obs in m.get("operational_observations", []):
                                    st.markdown(f"• {obs}")

                            st.markdown("---")
            else:
                st.error("Comparison computation failed.")
