"""
Python wrapper for C# DaxExecutor subprocess.
Integrates with existing query_executor infrastructure.
"""
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DaxExecutorWrapper:
    """
    Wrapper for C# DaxExecutor providing performance profiling capabilities.
    Integrates with existing infrastructure.
    """

    def __init__(self):
        self.executor_path = self._find_executor()

    def _find_executor(self) -> Path:
        """Locate DaxExecutor.exe in infrastructure directory"""
        base_path = Path(__file__).parent / "dax_executor"
        exe_path = base_path / "bin" / "Release" / "net8.0" / "DaxExecutor.exe"

        if not exe_path.exists():
            raise FileNotFoundError(
                f"DaxExecutor.exe not found at {exe_path}. "
                "Run core/infrastructure/dax_executor/build.bat first."
            )

        return exe_path

    def execute_with_profiling(
        self,
        query: str,
        xmla_endpoint: str,
        dataset_name: str,
        access_token: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Execute DAX query with performance profiling.

        Args:
            query: DAX query to execute
            xmla_endpoint: XMLA endpoint URL
            dataset_name: Dataset/database name
            access_token: Optional access token (None for desktop)
            timeout_seconds: Execution timeout in seconds

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            # Build command (no token in args - security!)
            cmd = [
                str(self.executor_path),
                "--xmla", xmla_endpoint,
                "--dataset", dataset_name,
                "--query", query,
                "--verbose"
            ]

            # Pass token via stdin for security
            token_input = access_token or "desktop-no-auth"

            # Execute subprocess
            result = subprocess.run(
                cmd,
                input=token_input,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )

            if result.returncode != 0:
                error_msg = f"DaxExecutor failed: {result.stderr.strip()}"
                logger.error(error_msg)
                return False, {}, error_msg

            # Parse JSON output
            try:
                result_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                # Try to extract JSON from mixed output
                result_data = self._extract_json(result.stdout)
                if not result_data:
                    return False, {}, f"Failed to parse output: {str(e)}"

            # Check for execution errors
            if not result_data.get("Success", True):
                error_msg = result_data.get("ErrorMessage", "DAX execution error")
                return False, result_data, error_msg

            return True, result_data, None

        except subprocess.TimeoutExpired:
            return False, {}, f"Execution timed out after {timeout_seconds}s"
        except FileNotFoundError:
            return False, {}, "DaxExecutor.exe not found. Please build it first using build.bat"
        except Exception as e:
            logger.exception("DaxExecutor wrapper error")
            return False, {}, str(e)

    def _extract_json(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from mixed stdout output"""
        try:
            lines = raw_output.split('\n')
            json_start = next(i for i, line in enumerate(lines) if line.strip().startswith('{'))
            json_end = next(i for i in range(len(lines)-1, json_start-1, -1)
                          if lines[i].strip().endswith('}'))

            json_str = '\n'.join(lines[json_start:json_end + 1])
            return json.loads(json_str)
        except Exception:
            return None
