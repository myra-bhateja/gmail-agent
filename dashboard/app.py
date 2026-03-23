import os
import sys
import time
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import run_query
from dotenv import load_dotenv

load_dotenv()

SHEET_URL = os.getenv('SHEET_PUBLIC_URL', '')

os.makedirs(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'
), exist_ok=True)

LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'agent_log.jsonl'
)
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()

try:
    _logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'galogo.png'
    )
    logo = Image.open(_logo_path)
except Exception:
    logo = None

st.set_page_config(
    page_title='Gmail Agent',
    page_icon=logo if logo else 'G',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ── About popup on first visit ────────────────────────────
if 'show_about' not in st.session_state:
    st.session_state['show_about'] = True

@st.dialog("Welcome to Gmail AI Agent", width="large")
def show_about_dialog():
    st.markdown("**by Myra Bhateja**")
    st.divider()
    st.markdown("""
    An end-to-end AI pipeline that connects to a Gmail inbox, extracts
    structured information from every email using Google Gemini 2.5 Flash,
    and organises it into a live dashboard, without any manual input.

    The agent runs on demand. For each email it identifies the sender's
    intent, assigns an urgency level, classifies the category, reads the
    sentiment, and flags whether action is needed - all in a single AI pass.
    Results are stored in both SQLite and Google Sheets simultaneously.

    Every processed email also comes with a suggested reply, generated
    automatically based on the email's content, tone, and required action.

    A separate multi-agent analysis pipeline lets you ask plain English
    questions about your inbox data. Four specialised agents work in sequence
    - Loader, Query, Analyst, and Visualiser, all triggered by one question.
    """)
    st.divider()
    st.markdown("""
    **Tech stack**
    - LLM — Google Gemini 2.5 Flash
    - Email source — Gmail API
    - Database — SQLite + Google Sheets
    - Dashboard — Streamlit + Plotly
    - Language — Python 3.11
    """)
    st.caption("Click X to close and get started. Visit the About page anytime.")

if st.session_state['show_about']:
    show_about_dialog()
    st.session_state['show_about'] = False

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
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stException"] button { display: none !important; }
[title="streamlit"] { display: none; }
[data-testid="stHeader"] {
    background-color: #fff0f5 !important;
    border-bottom: 1px solid #f4c0d1 !important;
}
[data-testid="stHeader"] button,
[data-testid="collapsedControl"],
[data-testid="collapsedControl"] button {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}
[data-testid="stHeader"] button svg,
[data-testid="collapsedControl"] svg {
    fill: #72243e !important;
    stroke: #72243e !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stModal"] {
    background: white !important;
}
[data-testid="stModal"] p {
    color: #333333 !important;
}
[data-testid="stModal"] h1,
[data-testid="stModal"] h2,
[data-testid="stModal"] h3 {
    color: #72243e !important;
}
[data-testid="stModal"] li {
    color: #333333 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background-color: #fff0f5;
    border-bottom: 2px solid #f4c0d1;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #993556;
    font-size: 14px;
    font-weight: 500;
    padding: 8px 20px;
    border-radius: 6px 6px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: #f4c0d1 !important;
    color: #72243e !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #d4537e !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #fbeaf0 !important;
    color: #72243e !important;
}
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
    max_emails = st.slider("Max emails to fetch", 2, 15, 5, step=1)

    if st.button("Run agent now", type='primary'):
        import threading
        from run_agent_once import run_once

        if 'agent_running' not in st.session_state:
            st.session_state['agent_running'] = False

        if not st.session_state['agent_running']:
            st.session_state['agent_running'] = True

            def run_in_background():
                run_once(max_emails=max_emails)
                st.session_state['agent_running'] = False

            thread = threading.Thread(target=run_in_background, daemon=True)
            thread.start()
            st.success("Agent started. Go to Live Agent Feed to watch progress.")
        else:
            st.warning("Agent is already running.")

    st.caption("This may take a moment depending on the number of emails.")

    st.divider()

    st.markdown("**Try it out**")
    st.caption("Want to see the agent in action?")
    st.markdown("1. Click below to send a test email")
    st.markdown("2. Click **Run agent now** above")
    st.markdown("3. Watch the Live Agent Feed tab update")

    gmail_link = (
        "https://mail.google.com/mail/?view=cm"
        "&to=bhatejamyra@gmail.com"
        "&su=Quick+question"
        "&body=Hi+Myra%2C%0A%0A"
        "I+wanted+to+check+in+about+our+meeting+next+week.+"
        "Could+you+confirm+if+Thursday+at+3pm+works+for+you%3F%0A%0A"
        "Also+let+me+know+if+you+need+any+documents+beforehand.%0A%0A"
        "Thanks%0A%0A"
        "%0A%0A"
        "This+is+a+trial+email+to+test+the+Gmail+AI+Agent+in+action.%0A%0A"
        "Feel+free+to+replace+this+with+any+real+scenario+%E2%80%94+a+meeting+request%2C+"
        "a+complaint%2C+an+urgent+ask%2C+or+a+sales+pitch.+%0A%0A"
        "The+agent+will+read+this+email+and+automatically+extract+the+intent%2C+"
        "urgency%2C+category%2C+sentiment%2C+and+suggest+a+reply.%0A%0A"
        "Give+it+a+try+and+see+what+it+picks+up."
    )

    st.markdown(
        f'<a href="{gmail_link}" target="_blank">'
        f'<button style="width:100%;background:#fff0f5;color:#72243e;'
        f'border:1px solid #f4c0d1;padding:6px 12px;border-radius:6px;'
        f'cursor:pointer;font-size:12px;font-weight:500;margin-top:6px">'
        f'Send test email</button></a>',
        unsafe_allow_html=True
    )
    st.caption("Opens Gmail in browser with receiver and subject pre-filled")

# ── Log helpers ───────────────────────────────────────────
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

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Live Agent Feed",
    "Email Log",
    "Ask the Agent",
    "About"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — Live Agent Feed
# ══════════════════════════════════════════════════════════
with tab1:
    st.title("Live Agent Feed")
    st.caption("Watch the agent process emails step by step.")
    st.info("Run the agent from the sidebar, then stay on this tab to watch emails being processed in real time. Once done, check the Email Log tab for full results.")

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
        st.markdown("**Live log** — newest first, refreshes every 2 seconds")
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

        if logs and logs[0].get('event_type') == 'db_sync' and logs[0].get('status') == 'success':
            st.success("Agent run complete. Head to the Email Log tab to see results.")

    st.caption("Auto-refreshing every 2 seconds...")
    if st.session_state.get('agent_running', False):
        time.sleep(2)
        st.rerun()
    else:
        if logs:
            time.sleep(2)
            st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 2 — Email Log
# ══════════════════════════════════════════════════════════
with tab2:
    st.title("Email Log")
    st.caption("All emails processed by the agent.")

    try:
        from tools.db import sync_from_sheets
        sync_from_sheets()
    except Exception:
        pass

    col_refresh, col_latest, _ = st.columns([1, 1, 4])
    with col_refresh:
        if st.button("Refresh"):
            st.rerun()
    with col_latest:
        show_latest = st.toggle("Latest run only")

    try:
        df = run_query("SELECT * FROM emails ORDER BY timestamp DESC")
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        st.warning("No emails yet. Click Run agent now in the sidebar.")
    else:
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], errors='coerce')
        latest_time        = df['timestamp_dt'].max()

        if pd.notna(latest_time) and len(df) > 1:
            df_sorted   = df.sort_values('timestamp_dt', ascending=False)
            time_diffs  = df_sorted['timestamp_dt'].diff().abs()
            big_gap_idx = time_diffs[time_diffs > pd.Timedelta(minutes=30)].index
            if len(big_gap_idx) > 0:
                cutoff_star = df_sorted.loc[big_gap_idx[0], 'timestamp_dt']
            else:
                cutoff_star = latest_time - pd.Timedelta(minutes=30)
        else:
            cutoff_star = latest_time

        # ── Latest emails at top ──────────────────────────
        st.subheader("Latest processed emails")
        st.caption("Emails from the most recent agent run are marked with a star.")

        filtered_top = df.copy()
        if show_latest and cutoff_star is not None:
            filtered_top = filtered_top[filtered_top['timestamp_dt'] >= cutoff_star]

        for idx, row in filtered_top.head(10).iterrows():
            subject = str(row.get('subject', 'No subject'))
            sender  = str(row.get('from',    'Unknown'))
            urgency = str(row.get('urgency', ''))
            is_new  = cutoff_star is not None and pd.notna(row['timestamp_dt']) and row['timestamp_dt'] >= cutoff_star
            star    = ' ★' if is_new else ''

            with st.expander(f"{subject}{star}  —  {sender}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**Urgency:** {urgency}")
                c2.markdown(f"**Category:** {row.get('category', '')}")
                c3.markdown(f"**Action:** {row.get('action_required', '')}")
                c4.markdown(f"**Sentiment:** {row.get('sentiment', '')}")

                if row.get('summary'):
                    st.markdown(f"**Summary:** {row.get('summary', '')}")

                st.divider()

                reply_key = f"reply_top_{idx}"
                if st.button("Generate reply", key=f"btn_top_{idx}"):
                    from llm_extractor import generate_reply
                    email_dict     = {'sender': row.get('from', ''), 'subject': row.get('subject', ''), 'body': row.get('summary', '')}
                    extracted_dict = {'category': row.get('category', ''), 'urgency': row.get('urgency', ''), 'action_required': row.get('action_required', ''), 'action_description': row.get('action_description', ''), 'sentiment': row.get('sentiment', '')}
                    with st.spinner("Generating reply..."):
                        reply = generate_reply(email_dict, extracted_dict)
                    st.session_state[reply_key] = reply

                if reply_key in st.session_state:
                    st.markdown("**Suggested reply:**")
                    st.markdown(f'<div style="background:#fff0f5;border:1px solid #f4c0d1;border-radius:8px;padding:14px;font-size:13px;color:#72243e;line-height:1.7;">{st.session_state[reply_key]}</div>', unsafe_allow_html=True)
                    st.code(st.session_state[reply_key], language=None)
                    st.caption("Copy the text above to use as your reply.")

        st.divider()

        # ── Analytics ─────────────────────────────────────
        st.subheader("Analytics")

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
                fig = px.pie(urg, names='Urgency', values='Count', color='Urgency',
                    color_discrete_map={'high': '#d4537e', 'medium': '#f4c0d1', 'low': '#fbeaf0'},
                    title='Urgency breakdown')
                fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

        with ch2:
            if 'category' in df.columns:
                cat = df['category'].value_counts().reset_index()
                cat.columns = ['Category', 'Count']
                fig2 = px.bar(cat, x='Category', y='Count', title='Emails by category',
                    color_discrete_sequence=['#d4537e'])
                fig2.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig2, use_container_width=True)

        with ch3:
            if 'sentiment' in df.columns:
                sent = df['sentiment'].value_counts().reset_index()
                sent.columns = ['Sentiment', 'Count']
                fig3 = px.pie(sent, names='Sentiment', values='Count', color='Sentiment',
                    color_discrete_map={'positive': '#993556', 'neutral': '#f4c0d1', 'negative': '#72243e'},
                    title='Sentiment breakdown')
                fig3.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig3, use_container_width=True)

        if 'timestamp' in df.columns:
            try:
                st.subheader("Emails over time")
                time_df              = df.copy()
                time_df['timestamp'] = pd.to_datetime(time_df['timestamp'], errors='coerce')
                time_df['Date']      = time_df['timestamp'].dt.date
                time_counts          = time_df.groupby('Date').size().reset_index(name='Count')
                fig_time             = px.line(time_counts, x='Date', y='Count', markers=True,
                    title='Emails processed per day', color_discrete_sequence=['#d4537e'])
                fig_time.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig_time, use_container_width=True)
            except Exception:
                pass

        st.divider()

        # ── All emails filtered ───────────────────────────
        st.subheader("All emails")

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

        if show_latest and cutoff_star is not None:
            filtered = filtered[filtered['timestamp_dt'] >= cutoff_star]

        if sel_urg != 'All' and 'urgency'         in df.columns: filtered = filtered[filtered['urgency']         == sel_urg]
        if sel_cat != 'All' and 'category'        in df.columns: filtered = filtered[filtered['category']        == sel_cat]
        if sel_act != 'All' and 'action_required' in df.columns: filtered = filtered[filtered['action_required'] == sel_act]

        for idx, row in filtered.iterrows():
            subject = str(row.get('subject', 'No subject'))
            sender  = str(row.get('from',    'Unknown'))
            urgency = str(row.get('urgency', ''))
            is_new  = cutoff_star is not None and pd.notna(row['timestamp_dt']) and row['timestamp_dt'] >= cutoff_star
            star    = ' ★' if is_new else ''

            with st.expander(f"{subject}{star}  —  {sender}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**Urgency:** {urgency}")
                c2.markdown(f"**Category:** {row.get('category', '')}")
                c3.markdown(f"**Action:** {row.get('action_required', '')}")
                c4.markdown(f"**Sentiment:** {row.get('sentiment', '')}")

                if row.get('summary'):
                    st.markdown(f"**Summary:** {row.get('summary', '')}")

                st.divider()

                reply_key = f"reply_{idx}"
                if st.button("Generate reply", key=f"btn_{idx}"):
                    from llm_extractor import generate_reply
                    email_dict     = {'sender': row.get('from', ''), 'subject': row.get('subject', ''), 'body': row.get('summary', '')}
                    extracted_dict = {'category': row.get('category', ''), 'urgency': row.get('urgency', ''), 'action_required': row.get('action_required', ''), 'action_description': row.get('action_description', ''), 'sentiment': row.get('sentiment', '')}
                    with st.spinner("Generating reply..."):
                        reply = generate_reply(email_dict, extracted_dict)
                    st.session_state[reply_key] = reply

                if reply_key in st.session_state:
                    st.markdown("**Suggested reply:**")
                    st.markdown(f'<div style="background:#fff0f5;border:1px solid #f4c0d1;border-radius:8px;padding:14px;font-size:13px;color:#72243e;line-height:1.7;">{st.session_state[reply_key]}</div>', unsafe_allow_html=True)
                    st.code(st.session_state[reply_key], language=None)
                    st.caption("Copy the text above to use as your reply.")

        st.divider()
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "emails.csv", "text/csv")

# ══════════════════════════════════════════════════════════
# TAB 3 — Ask the Agent
# ══════════════════════════════════════════════════════════
with tab3:
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
# TAB 4 — About
# ══════════════════════════════════════════════════════════
with tab4:
    st.title("About this project")
    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
        ### Gmail AI Agent

        An end-to-end AI pipeline that connects to a Gmail inbox, extracts
        structured information from every email using Google Gemini 2.5 Flash,
        and organises it into a live dashboard — without any manual input.

        The agent runs on demand. For each email it identifies the sender's
        intent, assigns an urgency level, classifies the category, reads the
        sentiment, and flags whether action is needed — all in a single AI pass.
        Results are stored in both SQLite and Google Sheets simultaneously.

        Every processed email also comes with a suggested reply, generated
        automatically based on the email's content, tone, and required action.
        No copy-pasting or context switching — the reply is ready the moment
        the email is classified.

        A separate multi-agent analysis pipeline lets you ask plain English
        questions about your inbox data. Four specialised agents work in sequence:
        the Loader Agent syncs the latest data, the Query Agent writes and runs
        real SQL against it, the Analyst Agent turns the numbers into a plain
        English insight, and the Visualiser Agent picks the right chart and
        generates it — all triggered by one question.

        ### Why it matters

        The average professional receives 120 emails a day and spends
        over 2 hours managing them. Manual triage — reading, categorising,
        and deciding what needs action — is repetitive and time-consuming.

        This agent processes each email in under 2 seconds using Gemini 2.5 Flash,
        extracting intent, urgency, category, sentiment, and required action in a
        single pass. At 50 emails a day that is over 90 minutes of triage time
        handed back daily.

        Beyond speed, the agent adds structure. Every email gets a category,
        an urgency level, a sentiment score, and a suggested action — making
        it easy to prioritise without opening a single email manually.

        ### Tech stack
        - LLM — Google Gemini 2.5 Flash
        - Email source — Gmail API
        - Database — SQLite + Google Sheets
        - Dashboard — Streamlit + Plotly
        - Language — Python 3.11
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