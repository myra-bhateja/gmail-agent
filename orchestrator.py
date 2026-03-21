import os
from datetime import datetime
from fpdf import FPDF
from tools.db import sync_from_sheets
from agents import loader_agent, query_agent, analyst_agent, visualiser_agent

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_pdf_report(question, analysis, chart_path, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 12, 'Data Analysis Report', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, 'Question', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, question)
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'Insight', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, analysis.get('insight', ''))
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'Key Findings', ln=True)
    pdf.set_font('Helvetica', '', 11)
    for finding in analysis.get('key_findings', []):
        pdf.multi_cell(0, 6, f"- {finding}")
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'Recommendation', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, analysis.get('recommendation', ''))
    pdf.ln(6)

    if chart_path and os.path.exists(chart_path):
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, 'Chart', ln=True)
        pdf.image(chart_path, w=180)

    pdf.output(output_path)
    print(f"[Orchestrator] PDF saved: {output_path}")

def run(question: str) -> dict:
    print(f"\n{'='*60}")
    print(f"ORCHESTRATOR STARTING")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    # Step 1 — Load
    loader_output = loader_agent.run(question)
    if 'error' in loader_output:
        return {'success': False, 'error': loader_output['error']}
    if not loader_output['assessment']['answerable']:
        return {'success': False, 'error': loader_output['assessment']['reason']}

    df     = loader_output['df']
    schema = loader_output['schema']

    # Step 2 — Query
    query_output = query_agent.run(question, df, schema)
    if not query_output['success']:
        return {'success': False, 'error': f"Query failed: {query_output.get('error')}"}

    query_result = query_output['result']

    # Step 3 — Analyse
    analysis = analyst_agent.run(question, query_result)

    # Step 4 — Visualise
    viz_output = visualiser_agent.run(
        question, df, query_result,
        analysis.get('chart_suggestion', 'bar'),
        analysis.get('insight', '')
    )

    # Step 5 — PDF
    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(OUTPUT_DIR, f'report_{timestamp}.pdf')
    chart_path  = viz_output.get('chart_path') if viz_output['success'] else None
    generate_pdf_report(question, analysis, chart_path, report_path)

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"Insight: {analysis['insight']}")
    print(f"{'='*60}")

    return {
        'success'        : True,
        'insight'        : analysis['insight'],
        'key_findings'   : analysis.get('key_findings', []),
        'recommendation' : analysis.get('recommendation', ''),
        'chart_path'     : chart_path,
        'report_path'    : report_path,
        'query_code'     : query_output['code']
    }

if __name__ == '__main__':
    question = input("Ask a question about your email data:\n> ")
    run(question)