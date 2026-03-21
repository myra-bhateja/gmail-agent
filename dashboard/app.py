import os
import sys
import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import run as run_pipeline
from tools.db import run_query, get_schema_description

st.set_page_config(page_title='Gmail Agent Dashboard', page_icon='📧', layout='wide')
st.title("📧 Gmail Agent + Multi-Agent Analysis")

tab1, tab2 = st.tabs(["📋 Email Log", "🤖 Ask the Agent"])

# ── Tab 1: Email log ──────────────────────────────────────
with tab1:
    st.subheader("All processed emails")

    if st.button("🔄 Refresh"):
        st.rerun()

    try:
        df = run_query("SELECT * FROM emails ORDER BY timestamp DESC")
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        st.warning("No emails yet. Run `python main.py` first.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total emails",    len(df))
        col2.metric("High urgency",    len(df[df.get('urgency', pd.Series()) == 'high']) if 'urgency' in df.columns else 0)
        col3.metric("Action required", len(df[df.get('action_required', pd.Series()) == 'yes']) if 'action_required' in df.columns else 0)
        col4.metric("Categories",      df['category'].nunique() if 'category' in df.columns else 0)

        st.divider()

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            urgencies  = ['All'] + sorted(df['urgency'].dropna().unique().tolist()) if 'urgency' in df.columns else ['All']
            sel_urg    = st.selectbox("Urgency", urgencies)
        with fc2:
            categories = ['All'] + sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else ['All']
            sel_cat    = st.selectbox("Category", categories)
        with fc3:
            actions    = ['All', 'yes', 'no']
            sel_act    = st.selectbox("Action required", actions)

        filtered = df.copy()
        if sel_urg != 'All' and 'urgency'         in df.columns: filtered = filtered[filtered['urgency']         == sel_urg]
        if sel_cat != 'All' and 'category'        in df.columns: filtered = filtered[filtered['category']        == sel_cat]
        if sel_act != 'All' and 'action_required' in df.columns: filtered = filtered[filtered['action_required'] == sel_act]

        st.dataframe(filtered, use_container_width=True, height=400)

        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "emails.csv", "text/csv")

# ── Tab 2: Multi-agent analysis ───────────────────────────
with tab2:
    st.subheader("Ask a question about your email data")
    st.caption("Four agents collaborate: Loader → Query → Analyst → Visualiser")

    examples = [
        "Which email category has the most high urgency emails?",
        "How many emails required action this week?",
        "What is the most common sentiment across all emails?",
        "Which senders emailed me the most?",
        "How many emails are in each category?"
    ]

    selected = st.selectbox("Pick an example or type your own:", [''] + examples)
    question = st.text_input("Your question:", value=selected)

    if st.button("▶ Run analysis", type='primary', disabled=not question):
        with st.status("Running multi-agent pipeline...", expanded=True) as status:
            st.write("🔵 Loader Agent — fetching and syncing data...")
            st.write("🟡 Query Agent — writing SQL query...")
            st.write("🟢 Analyst Agent — interpreting results...")
            st.write("🟣 Visualiser Agent — generating chart...")
            result = run_pipeline(question)
            status.update(label="Done!", state="complete")

        if not result['success']:
            st.error(f"Failed: {result.get('error')}")
        else:
            st.subheader("💡 Insight")
            st.info(result['insight'])

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📌 Key findings")
                for f in result.get('key_findings', []):
                    st.markdown(f"- {f}")
            with c2:
                st.subheader("✅ Recommendation")
                st.success(result.get('recommendation', ''))

            if result.get('chart_path') and os.path.exists(result['chart_path']):
                st.subheader("📊 Chart")
                st.image(result['chart_path'], use_column_width=True)

            with st.expander("🔍 SQL query Claude wrote"):
                st.code(result.get('query_code', ''), language='sql')

            if result.get('report_path') and os.path.exists(result['report_path']):
                with open(result['report_path'], 'rb') as f:
                    st.download_button("⬇️ Download PDF report", f,
                                       os.path.basename(result['report_path']),
                                       "application/pdf")
