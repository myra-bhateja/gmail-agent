import os
import sys
import time
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import run_query
from dotenv import load_dotenv

load_dotenv()

SHEET_URL = os.getenv('SHEET_PUBLIC_URL', '')

st.set_page_config(
    page_title='Gmail Agent',
    page_icon='../galogo.png',    # if you have a logo image
    layout='wide'
)

# ── Pink theme ────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #fff0f5;
}
[data-testid="stSidebar"] * {
    color: #72243e !important;
}
.stRadio label {
    font-size: 13px !important;
}
.stMetric {
    background: #fff0f5;
    border: 1px solid #f4c0d1;
    border-radius: 8px;
    padding: 12px;
}
.stMetricLabel { color: #993556 !important; font-size: 12px !important; }
.stMetricValue { color: #72243e !important; }
div[data-testid="stSelectbox"] select {
    background: #fff0f5;
    border-color: #f4c0d1;
    color: #72243e;
}
.stButton button {
    background: #fff0f5;
    border: 1px solid #f4c0d1;
    color: #72243e;
    padding: 4px 14px;
    font-size: 13px;
    border-radius: 6px;
}
.stButton button:hover {
    background: #f4c0d1;
    border-color: #d4537e;
}
.stDownloadButton button {
    background: #fff0f5;
    border: 1px solid #f4c0d1;
    color: #72243e;
    font-size: 13px;
    border-radius: 6px;
}
h1, h2, h3 { color: #72243e !important; }
.stInfo    { background: #fbeaf0; border-color: #f4c0d1; color: #72243e; }
.stSuccess { background: #fbeaf0; border-color: #f4c0d1; color: #72243e; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stException"] button { display: none !important; }
[data-testid="stSidebarNav"] { display: none; }
[title="streamlit"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Gmail AI Agent")
    st.markdown("**Myra Bhateja**")
    st.divider()

    if SHEET_URL:
        st.markdown(
            f'<a href="{SHEET_URL}" target="_blank">'
            f'<button style="width:100%;background:#f4c0d1;color:#72243e;border:1px solid #f4c0d1;'
            f'padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:500">'
            f'View Google Sheet</button></a>',
            unsafe_allow_html=True
        )
        st.caption("Opens in new tab — updates in real time")

    st.divider()

    st.markdown("**Agent**")
    max_emails = st.slider("Max emails to fetch", 5, 15, 10, step=5)

    if st.button("Run agent now", type='primary'):
        from run_agent_once import run_once
        with st.spinner("Agent running..."):
            summary = run_once(max_emails=max_emails)
        st.success(summary['message'])
        time.sleep(1)
        st.rerun()

    st.caption("This may take a moment depending on the number of emails.")

    st.divider()

    st.markdown("**Try it out**")
    st.caption("Want to see the agent in action?")
    st.markdown("1. Click below to send a test email")
    st.markdown("2. Click **Run agent now** above")
    st.markdown("3. Watch the Live Agent Feed update")

    test_subject = "Gmail Agent Trial"
    test_body    = "Hi, this is a test email to see the Gmail AI Agent in action.Please add content that is somewhat varied to test the agent's ability to extract different categories, urgencies, and sentiments. Thanks!"
    mailto_link  = (
        f"mailto:myrabhateja@gmail.com"
        f"?subject={test_subject.replace(' ', '%20')}"
        f"&body={test_body.replace(' ', '%20').replace(',', '%2C')}"
    )

    st.markdown(
        f'<a href="{mailto_link}" target="_blank">'
        f'<button style="width:100%;background:#fff0f5;color:#72243e;'
        f'border:1px solid #f4c0d1;padding:6px 12px;border-radius:6px;'
        f'cursor:pointer;font-size:12px;font-weight:500;margin-top:6px">'
        f'Send test email</button></a>',
        unsafe_allow_html=True
    )
    st.caption("Opens your Gmail with receiver and subject pre-filled")

    st.divider()

    page = st.radio(
        label='',
        options=[
            "Live Agent Feed",
            "Email Log",
            "Ask the Agent",
            "About"
        ]
    )

# ── Log helpers ───────────────────────────────────────────
LOG_FILE = os.path.join('data', 'agent_log.jsonl')
os.makedirs('data', exist_ok=True)

def write_log(event_type, message, detail='', status='info'):
    entry = {
        'time'      : datetime.now().strftime('%H:%M:%S'),
        'event_type': event_type,
        'message'   : message,
        'detail'    : detail,
        'status'    : status
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def read_logs(last_n=50):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = []
    for line in lines[-last_n:]:
        try:
            entries.append(json.loads(line.strip()))
        except Exception:
            continue
    return entries[::-1]

def clear_logs():
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

# ══════════════════════════════════════════════════════════
# PAGE 1 — Live Agent Feed
# ══════════════════════════════════════════════════════════
if page == "Live Agent Feed":
    st.title("Live Agent Feed")
    st.caption("Watch the agent process emails step by step.")

    col_a, col_b = st.columns([1, 3])

    with col_a:
        st.markdown("**Agent status**")
        logs        = read_logs(100)
        event_types = [l['event_type'] for l in logs[:20]]

        def agent_badge(name, trigger):
            if trigger in event_types:
                return f"● {name}"
            return f"○ {name}"

        st.markdown(agent_badge("Gmail Reader",  "gmail_read"))
        st.markdown(agent_badge("Gemini AI",     "llm_extract"))
        st.markdown(agent_badge("Router",        "route"))
        st.markdown(agent_badge("Sheets Writer", "sheets_write"))
        st.markdown(agent_badge("DB Sync",       "db_sync"))

        st.divider()

        total_processed = len([l for l in logs if l['event_type'] == 'llm_extract' and l['status'] == 'success'])
        total_errors    = len([l for l in logs if l['status'] == 'error'])

        st.metric("Processed", total_processed)
        st.metric("Errors",    total_errors)

        if st.button("Clear log"):
            clear_logs()
            st.rerun()

    with col_b:
        st.markdown("**Live log** — newest first, refreshes every 3 seconds")
        logs = read_logs(30)

        STATUS_LABEL = {
            'info'   : 'info',
            'success': 'ok',
            'error'  : 'error',
            'warning': 'warn'
        }

        if not logs:
            st.info("No activity yet. Click Run agent now in the sidebar.")
        else:
            rows = []
            for log in logs:
                label  = STATUS_LABEL.get(log['status'], 'info')
                detail = f" — {log['detail'][:80]}" if log['detail'] else ''
                rows.append({
                    'Time'   : log['time'],
                    'Status' : label,
                    'Event'  : log['event_type'],
                    'Message': log['message'] + detail
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)

    st.caption("Auto-refreshing every 3 seconds...")
    time.sleep(3)
    st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE 2 — Email Log
# ══════════════════════════════════════════════════════════
elif page == "Email Log":
    st.title("Email Log")
    st.caption("All emails processed by the agent.")

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("Refresh"):
            st.rerun()

    try:
        df = run_query("SELECT * FROM emails ORDER BY timestamp DESC")
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        st.warning("No emails yet. Click Run agent now in the sidebar.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total",         len(df))
        col2.metric("High urgency",  len(df[df['urgency'] == 'high'])        if 'urgency'         in df.columns else 0)
        col3.metric("Action needed", len(df[df['action_required'] == 'yes']) if 'action_required' in df.columns else 0)
        col4.metric("Categories",    df['category'].nunique()                if 'category'        in df.columns else 0)

        st.divider()

        ch1, ch2, ch3 = st.columns(3)

        with ch1:
            if 'urgency' in df.columns:
                urg = df['urgency'].value_counts().reset_index()
                urg.columns = ['Urgency', 'Count']
                fig = px.pie(
                    urg, names='Urgency', values='Count',
                    color='Urgency',
                    color_discrete_map={
                        'high'  : '#d4537e',
                        'medium': '#f4c0d1',
                        'low'   : '#fbeaf0'
                    },
                    title='Urgency breakdown'
                )
                fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

        with ch2:
            if 'category' in df.columns:
                cat = df['category'].value_counts().reset_index()
                cat.columns = ['Category', 'Count']
                fig2 = px.bar(
                    cat, x='Category', y='Count',
                    title='Emails by category',
                    color_discrete_sequence=['#d4537e']
                )
                fig2.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig2, use_container_width=True)

        with ch3:
            if 'sentiment' in df.columns:
                sent = df['sentiment'].value_counts().reset_index()
                sent.columns = ['Sentiment', 'Count']
                fig3 = px.pie(
                    sent, names='Sentiment', values='Count',
                    color='Sentiment',
                    color_discrete_map={
                        'positive': '#993556',
                        'neutral' : '#f4c0d1',
                        'negative': '#72243e'
                    },
                    title='Sentiment breakdown'
                )
                fig3.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig3, use_container_width=True)

        if 'timestamp' in df.columns:
            try:
                st.subheader("Emails over time")
                time_df               = df.copy()
                time_df['timestamp']  = pd.to_datetime(time_df['timestamp'], errors='coerce')
                time_df['Date']       = time_df['timestamp'].dt.date
                time_counts           = time_df.groupby('Date').size().reset_index(name='Count')
                fig_time              = px.line(
                    time_counts, x='Date', y='Count',
                    markers=True,
                    title='Emails processed per day',
                    color_discrete_sequence=['#d4537e']
                )
                fig_time.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig_time, use_container_width=True)
            except Exception:
                pass

        st.divider()
        st.subheader("Filter emails")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            urgencies = ['All'] + sorted(df['urgency'].dropna().unique().tolist()) if 'urgency' in df.columns else ['All']
            sel_urg   = st.selectbox("Urgency", urgencies)
        with fc2:
            cats    = ['All'] + sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else ['All']
            sel_cat = st.selectbox("Category", cats)
        with fc3:
            sel_act = st.selectbox("Action required", ['All', 'yes', 'no'])

        filtered = df.copy()
        if sel_urg != 'All' and 'urgency'         in df.columns: filtered = filtered[filtered['urgency']         == sel_urg]
        if sel_cat != 'All' and 'category'        in df.columns: filtered = filtered[filtered['category']        == sel_cat]
        if sel_act != 'All' and 'action_required' in df.columns: filtered = filtered[filtered['action_required'] == sel_act]

        st.dataframe(filtered, use_container_width=True, height=400)

        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "emails.csv", "text/csv")

# ══════════════════════════════════════════════════════════
# PAGE 3 — Ask the Agent
# ══════════════════════════════════════════════════════════
elif page == "Ask the Agent":
    st.title("Ask the Agent")
    st.caption("Four agents collaborate to answer questions about your email data.")

    examples = [
        "Which email category has the most high urgency emails?",
        "How many emails required action?",
        "What is the most common sentiment?",
        "Which senders emailed me the most?",
        "How many emails are in each category?",
        "How has email volume changed over time?"
    ]

    st.markdown("**Example questions**")
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        with cols[i % 3]:
            if st.button(ex, key=f"ex_{i}"):
                st.session_state['question'] = ex

    st.divider()

    question = st.text_input(
        "Your question:",
        value=st.session_state.get('question', ''),
        placeholder="Type a question about your emails..."
    )

    if st.button("Run analysis", type='primary', disabled=not question):
        from orchestrator import run as run_pipeline

        with st.status("Running pipeline...", expanded=True) as status:
            st.write("Loader Agent — syncing data...")
            st.write("Query Agent — writing SQL...")
            st.write("Analyst Agent — interpreting results...")
            st.write("Visualiser Agent — generating chart...")
            result = run_pipeline(question)
            status.update(label="Done.", state="complete")

        if not result['success']:
            st.error(f"Could not answer: {result.get('error')}")
        else:
            st.divider()

            st.subheader("Insight")
            st.info(result['insight'])

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Key findings")
                for f in result.get('key_findings', []):
                    st.markdown(f"- {f}")
            with c2:
                st.subheader("Recommendation")
                st.success(result.get('recommendation', ''))

            if result.get('chart_path') and os.path.exists(result['chart_path']):
                st.subheader("Chart")
                st.image(result['chart_path'], use_column_width=True)

            with st.expander("SQL query the agent wrote"):
                st.code(result.get('query_code', ''), language='sql')

# ══════════════════════════════════════════════════════════
# PAGE 4 — About   #Reading and triaging a single email manually takes around 2 minutes on average.      This gent processes one email in 6 seconds — extracting intent, urgency,         category, sentiment, and action in a ingle pass. That is a 20x speed         improvement per email. At 50 emails a day, this saves over an hour of         manual triage daily.
# ══════════════════════════════════════════════════════════
elif page == "About":
    st.title("About this project")
    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
        ### Gmail AI Agent

        An end-to-end AI pipeline that reads a Gmail inbox, extracts structured
        information using Google Gemini 2.5 Flash, stores it in SQLite and Google
        Sheets, and surfaces it through this dashboard.

        The agent runs on demand and classifies each email by intent, urgency,
        category, sentiment, and required action - entirely automatically with no
        human input.

        A second pipeline allows plain English questions to be asked about the data.
        Four specialised agents collaborate to answer each question: a Loader Agent
        syncs the data, a Query Agent writes and executes real SQL, an Analyst Agent
        interprets results, and a Visualiser Agent generates the chart.

        ### Why it matters

        

        ### Tech stack
        - LLM - Google Gemini 2.5 Flash
        - Email source - Gmail API
        - Database - SQLite + Google Sheets
        - Dashboard - Streamlit + Plotly
        - Language - Python 3.11
        """)

    with col_right:
        st.markdown("""
        <div style="background:#fff0f5;border:1px solid #f4c0d1;border-radius:10px;
                    padding:20px;text-align:center;">
            <div style="width:48px;height:48px;border-radius:50%;background:#f4c0d1;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:600;font-size:15px;color:#72243e;margin:0 auto 12px">
                MB
            </div>
            <div style="font-size:16px;font-weight:600;color:#72243e;margin-bottom:14px">
                Myra Bhateja
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if SHEET_URL:
            st.markdown(
                f'<a href="{SHEET_URL}" target="_blank">'
                f'<button style="width:100%;background:#f4c0d1;color:#72243e;'
                f'border:1px solid #f4c0d1;padding:6px 12px;border-radius:6px;'
                f'cursor:pointer;font-size:12px;font-weight:500">'
                f'View Google Sheet</button></a>',
                unsafe_allow_html=True
            )

    st.divider()
    st.caption("Gmail AI Agent · Myra Bhateja · Powered by Google Gemini 2.5 Flash")