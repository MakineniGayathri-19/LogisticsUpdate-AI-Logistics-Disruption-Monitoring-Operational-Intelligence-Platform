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
        # Display Current Event Card
        st.markdown(
            f"""
            <div style="background-color: #0F172A; border: 1px solid #38BDF8; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <span style="background-color: #0284C7; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">CURRENT DISRUPTION BENCHMARK</span>
                <h3 style="color: #F8FAFC; margin-top: 8px; margin-bottom: 4px;">{current_event.get('title')}</h3>
                <p style="color: #CBD5E1; font-size: 0.9rem;">{current_event.get('description')}</p>
                <div style="display: flex; gap: 20px; font-size: 0.85rem; color: #94A3B8;">
                    <span><b>Category:</b> {current_event.get('category')}</span>
                    <span><b>Location:</b> {current_event.get('location')}</span>
                    <span><b>Severity:</b> {current_event.get('severity')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

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

                        # Color code match score
                        score_color = "#10B981" if sim_pct >= 40 else "#F59E0B" if sim_pct >= 20 else "#64748B"

                        with st.container():
                            st.markdown(
                                f"""
                                <div style="background-color: #1E293B; border-left: 6px solid {score_color}; padding: 16px; border-radius: 6px; margin-bottom: 18px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC;">#{i} Precedent: {m.get('title')}</span>
                                        <span style="background-color: {score_color}; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">
                                            {sim_pct:.1f}% Similarity
                                        </span>
                                    </div>
                                    <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                                        Category: {m.get('category')} &nbsp;|&nbsp; Location: {m.get('location')}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
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
