import os
from datetime import datetime
from tools.db import sync_from_sheets
from agents import loader_agent, query_agent, analyst_agent, visualiser_agent

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

    chart_path = viz_output.get('chart_path') if viz_output and viz_output.get('success') else None

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
        'query_code'     : query_output['code']
    }

if __name__ == '__main__':
    question = input("Ask a question about your email data:\n> ")
    run(question)