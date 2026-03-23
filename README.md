# Gmail AI Agent
**Built by Myra Bhateja**

An AI pipeline that reads a Gmail inbox, classifies every email, generates suggested replies, and displays everything on a live dashboard.

## Features
- Reads unread emails on demand
- Extracts urgency, category, sentiment, intent and action using Gemini 2.5 Flash
- Auto-generates a reply for each email
- Ask plain English questions about your inbox data
- Live processing feed + analytics dashboard

## Tech stack
Python · Google Gemini 2.5 Flash · Gmail API · SQLite · Google Sheets · Streamlit · Plotly

## Run locally

1. Clone the repo
2. Create and activate a virtual environment
```
   python -m venv venv
   venv\Scripts\activate
```
3. Install dependencies
```
   pip install -r requirements.txt
```
4. Create a `.env` file in the project root
```
   GEMINI_API_KEY=your_gemini_key
   SHEET_ID=your_google_sheet_id
   SHEET_PUBLIC_URL=your_google_sheet_url
```
5. Add `credentials.json` from Google Cloud Console to the project root
6. Run the dashboard
```
   streamlit run dashboard/app.py
```
7. On first run a browser window will open — sign in with the Gmail account you want to monitor