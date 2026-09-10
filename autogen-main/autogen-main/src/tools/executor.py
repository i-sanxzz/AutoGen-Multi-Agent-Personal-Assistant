"""Local Python code execution tool wrapped around AutoGen's LocalCommandLineCodeExecutor."""

import warnings
from pathlib import Path

# Suppress local execution security warning for clean terminal outputs during demo/review
warnings.filterwarnings("ignore", message=".*LocalCommandLineCodeExecutor.*")

from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

# Dedicated workspace directory for execution artifacts
WORKSPACE_DIR = Path("workspace").resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# Shared executor instance with 30s execution timeout
_executor = LocalCommandLineCodeExecutor(
    work_dir=WORKSPACE_DIR,
    timeout=30
)


async def execute_python_code(code: str) -> str:
    """Executes Python code in a local workspace environment and returns stdout and stderr.
    
    Args:
        code: The Python code snippet to execute.

    Returns:
        The execution output (stdout/stderr) and exit status.
    """
    if not code or not code.strip():
        return "Execution error: No code provided to execute."

    try:
        block = CodeBlock(language="python", code=code)
        token = CancellationToken()
        result = await _executor.execute_code_blocks([block], cancellation_token=token)
        
        status = "SUCCESS" if result.exit_code == 0 else f"FAILED (Exit code: {result.exit_code})"
        output = result.output.strip() if result.output else "(No standard output)"
        
        return f"Execution Status: {status}\nOutput:\n{output}"
    except Exception as e:
        return f"Execution error: {str(e)}"
