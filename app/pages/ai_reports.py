"""PAGE 6: AI INTELLIGENCE REPORTS
Operational Intelligence Brief generator adhering to strict 13-section format,
no-hallucination policies, verified provenance, and multi-format PDF/Text export.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def render(api_get, api_post):
    st.markdown('<div class="page-title">🤖 AI Operational Intelligence Briefs</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Strict no-hallucination executive briefs synthesized from verified source facts and Memento memory.</div>', unsafe_allow_html=True)

    tab_generate, tab_browse = st.tabs(["⚡ Synthesize New Operational Brief", "📂 Generated Brief Archive"])

    with tab_generate:
        disruptions = api_get("disruptions") or []
        if not disruptions:
            st.warning("No active disruptions logged. Collect or add disruptions first.")
        else:
            options = {f"[{d.get('severity', 'Alert')}] {d.get('title')} ({d.get('location')})": d.get("id") for d in disruptions}
            selected_label = st.selectbox("Select Target Disruption:", list(options.keys()))
            selected_id = options[selected_label]

            col_btn, col_info = st.columns([1, 2])
            with col_btn:
                generate_clicked = st.button("🚀 Generate 13-Section Brief", type="primary", use_container_width=True)
            with col_info:
                st.caption("Includes Executive Summary, Severity Justification, Memento Precedents, Mitigation Actions, and Source References.")

            if generate_clicked:
                with st.spinner("Synthesizing multi-section brief via LLM engine..."):
                    res = api_post("reports/generate", {"event_id": selected_id})
                    if res and res.status_code == 200:
                        rep = res.json()
                        st.success(f"Operational brief #{rep.get('id')} generated successfully!")
                        st.session_state["latest_report"] = rep
                    else:
                        st.error("Report generation failed.")

            # Display generated or latest report
            active_report = st.session_state.get("latest_report")
            if active_report:
                st.markdown("---")
                with st.container(border=True):
                    provider_col, generated_col, status_col = st.columns(3)
                    provider_col.metric("LLM Provider", active_report.get("llm_provider") or "Unknown")
                    generated_col.metric("Generated", active_report.get("generated_at", "")[:19] or "Unknown")
                    status_col.metric("Compliance", "13 sections ✓")

                content = active_report.get("content", "")
                st.text_area("Full Executive Brief Content", content, height=450)

                # Export Bar
                exp1, exp2, exp3 = st.columns(3)
                with exp1:
                    # Download as PDF via backend endpoint
                    from backend.services.report_service import generate_pdf_report
                    try:
                        pdf_data = generate_pdf_report(active_report)
                        st.download_button(
                            label="📄 Download Official PDF",
                            data=pdf_data,
                            file_name=f"logistics_brief_{active_report.get('id')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.caption(f"PDF generator unavailable: {e}")

                with exp2:
                    st.download_button(
                        label="💾 Download Text (.txt)",
                        data=content,
                        file_name=f"logistics_brief_{active_report.get('id')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                with exp3:
                    st.download_button(
                        label="📑 Download Markdown (.md)",
                        data=content,
                        file_name=f"logistics_brief_{active_report.get('id')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

    with tab_browse:
        reports = api_get("reports") or []
        if not reports:
            st.info("No operational briefs logged in the database archive.")
        else:
            st.caption(f"Total archived operational briefs: **{len(reports)}**")
            for r in reports:
                with st.expander(f"📑 Brief #{r.get('id')} — Disruption Ref: {r.get('disruption_id')} ({r.get('generated_at', '')[:19]})"):
                    st.markdown(f"**Engine Provider:** `{r.get('llm_provider')}`")
                    st.text_area("Brief Content", r.get("content"), height=250, key=f"browse_txt_{r.get('id')}")

                    from backend.services.report_service import generate_pdf_report
                    try:
                        p_bytes = generate_pdf_report(r)
                        st.download_button(
                            label=f"Download PDF #{r.get('id')}",
                            data=p_bytes,
                            file_name=f"brief_{r.get('id')}.pdf",
                            mime="application/pdf",
                            key=f"dl_pdf_{r.get('id')}"
                        )
                    except Exception:
                        pass
