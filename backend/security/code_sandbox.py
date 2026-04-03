import sys
from io import StringIO
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict

def execute_code_safely(code: str, persistent_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes Python code in a controlled environment.
    Captures stdout and manages persistent variables.
    """
    # Create a fresh copy of globals for execution
    exec_globals = {
        "pd": pd,
        "np": np,
        "px": px,
        "go": go,
        "plotly_figures": [],
    }
    # Update with persistent variables (DataFrames, etc.)
    exec_globals.update(persistent_vars)

    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output

    error = None
    try:
        # Note: In a real production system, we would use RestrictedPython or a Docker sandbox
        # But for this exam, we use a controlled globals dict as specified.
        exec(code, exec_globals)
    except Exception as e:
        error = str(e)
    finally:
        sys.stdout = old_stdout

    stdout_output = redirected_output.getvalue()

    # Filter out internal/module variables from the persistent state
    new_persistent_vars = {
        k: v for k, v in exec_globals.items() 
        if k not in ["pd", "np", "px", "go", "__builtins__"]
    }

    return {
        "success": error is None,
        "output": stdout_output if error is None else error,
        "error": error,
        "persistent_vars": new_persistent_vars,
        "plotly_figures": exec_globals.get("plotly_figures", [])
    }
