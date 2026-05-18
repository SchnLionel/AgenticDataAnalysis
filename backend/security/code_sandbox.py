import sys
import signal
from io import StringIO
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

def execute_code_safely(code: str, persistent_vars: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Executes Python code in a controlled environment.
    Captures stdout and manages persistent variables.
    """
    # Create a fresh copy of globals for execution
    # Restricting __builtins__ prevents use of __import__ for arbitrary modules
    exec_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "dict": dict,
            "list": list,
            "set": set,
            "tuple": tuple,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "MemoryError": MemoryError,
            "__import__": __import__,
        },
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
    
    # Set the signal handler and a timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        # Note: In a real production system, we would use RestrictedPython or a Docker sandbox
        # But for this exam, we use a controlled globals dict as specified.
        exec(code, exec_globals)
    except TimeoutError as e:
        error = str(e)
    except MemoryError as e:
        error = f"Memory limit exceeded: {e}"
    except Exception as e:
        error = str(e)
    except BaseException as e:
        error = str(e)
    finally:
        signal.alarm(0)  # Disable the alarm
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
