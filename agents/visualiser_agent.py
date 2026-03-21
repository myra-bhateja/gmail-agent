import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run(question: str, df: pd.DataFrame, query_result,
        chart_suggestion: str, insight: str) -> dict:

    print(f"[Visualiser Agent] Generating {chart_suggestion} chart...")

    if isinstance(query_result, pd.DataFrame):
        result_str = query_result.to_string(index=False)
        columns    = list(query_result.columns)
    else:
        result_str = str(query_result)
        columns    = []

    prompt = f"""
You are a data visualisation agent. Write Plotly Express code to visualise
the data below.

QUESTION: {question}
CHART TYPE: {chart_suggestion}
COLUMNS AVAILABLE: {columns}

DATA:
{result_str}

Rules:
- Use plotly.express (imported as px) or plotly.graph_objects (imported as go)
- query_result is already a DataFrame available as variable 'query_result'
- Assign your figure to a variable called 'result'
- Add a descriptive title
- Do NOT call fig.show() or fig.write_image()
- Raw Python code only, no markdown fences

Example:
result = px.bar(query_result, x='{columns[0] if columns else "x"}',
                y='{columns[1] if len(columns) > 1 else "y"}',
                title='Your title here')
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    code = response.text.strip().replace('```python', '').replace('```', '').strip()

    local_scope = {'query_result': query_result, 'px': px, 'go': go, 'pd': pd}

    try:
        exec(code, {}, local_scope)
        exec(code, {}, local_scope)
        fig = local_scope.get('result')

        if fig is None:
            return {'success': False, 'error': 'No figure assigned to result'}

        # Force white background so saved PNG is not black
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font_color='black'
        )

        chart_path = os.path.join(OUTPUT_DIR, 'chart.png')
        fig.write_image(chart_path, width=900, height=500, scale=2)
        
    except Exception as e:
        return {'success': False, 'error': str(e)}