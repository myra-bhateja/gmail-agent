import pandas as pd
import traceback

def execute_pandas_code(code: str, df: pd.DataFrame) -> dict:
    local_scope = {'df': df.copy(), 'pd': pd}
    try:
        exec(code, {}, local_scope)
        if 'result' not in local_scope:
            return {
                'success': False,
                'result' : None,
                'error'  : "Code must assign output to a variable called 'result'"
            }
        return {'success': True, 'result': local_scope['result'], 'error': None}
    except Exception:
        return {'success': False, 'result': None, 'error': traceback.format_exc()}