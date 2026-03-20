"""
Agent 1: Log Analysis Agent
Input : raw log strings from 3 files
Output: LogAnalysisOutput (Pydantic)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.schemas import LogAnalysisOutput
from services.llm import call_llm_json
from config import LOG_CHUNK_SIZE


PROMPT_TEMPLATE = """You are a senior site reliability engineer performing root cause analysis.

You have been given logs from three sources:

=== NGINX ACCESS LOG ===
{nginx_access}

=== NGINX ERROR LOG ===
{nginx_error}

=== APPLICATION ERROR LOG ===
{app_error}

Your task:
1. Identify ALL anomalies: 5xx errors, timeouts, repeated failures, worker crashes, resource exhaustion
2. Determine the most likely root cause by correlating events across all three log sources
3. Extract the 5 strongest evidence snippets (exact log lines) that prove the root cause
4. State 1-2 alternate hypotheses
5. List all affected API endpoints
6. Write a 2-sentence timeline summary of what happened

Return this exact JSON structure:
{{
  "suspected_root_cause": "One clear sentence stating the primary root cause",
  "evidence": [
    "exact log line 1 with timestamp",
    "exact log line 2 with timestamp",
    "exact log line 3 with timestamp",
    "exact log line 4 with timestamp",
    "exact log line 5 with timestamp"
  ],
  "confidence": 0.0,
  "alternate_hypotheses": [
    "hypothesis 1",
    "hypothesis 2"
  ],
  "affected_endpoints": ["/api/v1/...", "..."],
  "timeline_summary": "Two sentence timeline of the incident."
}}

Be precise. confidence must be between 0.0 and 1.0.
"""


def _chunk_log(content: str, max_size: int = LOG_CHUNK_SIZE) -> str:
    """Return the most relevant portion of a log if it's too large."""
    if len(content) <= max_size:
        return content
    # Keep last portion (most recent events are most relevant)
    return "...[truncated for length]...\n" + content[-max_size:]


def run(logs: dict[str, str]) -> LogAnalysisOutput:
    """
    Args:
        logs: dict with keys 'nginx_access', 'nginx_error', 'app_error'
    Returns:
        LogAnalysisOutput
    """
    prompt = PROMPT_TEMPLATE.format(
        nginx_access=_chunk_log(logs.get("nginx_access", "")),
        nginx_error=_chunk_log(logs.get("nginx_error", "")),
        app_error=_chunk_log(logs.get("app_error", "")),
    )

    result = call_llm_json(prompt)
    return LogAnalysisOutput(**result)


if __name__ == "__main__":
    # Quick standalone test
    from config import LOG_FILES
    logs = {}
    for key, path in LOG_FILES.items():
        with open(path) as f:
            logs[key] = f.read()
    out = run(logs)
    import json
    print(json.dumps(out.model_dump(), indent=2))
