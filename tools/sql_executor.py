from tools.db import run_query

def execute_sql(sql: str) -> dict:
    sql = sql.strip()

    if not sql.upper().startswith('SELECT'):
        return {
            'success': False,
            'result' : None,
            'error'  : 'Only SELECT queries are allowed.'
        }

    try:
        result = run_query(sql)
        return {'success': True, 'result': result, 'error': None}
    except Exception as e:
        return {'success': False, 'result': None, 'error': str(e)}