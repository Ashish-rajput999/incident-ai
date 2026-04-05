"""
Agent 3: Resolution Planner Agent
Input : LogAnalysisOutput + ResearchOutput
Output: PlannerOutput (Pydantic)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.schemas import LogAnalysisOutput, ResearchOutput, PlannerOutput, RemediationStep
from services.llm import call_llm_json


PLANNER_PROMPT = """You are a senior production engineer creating a detailed incident remediation plan.

=== INCIDENT ANALYSIS ===
Root Cause: {root_cause}
Confidence: {confidence}
Affected Endpoints: {affected_endpoints}
Evidence:
{evidence}

Timeline: {timeline}

=== AVAILABLE SOLUTIONS (from research) ===
{solutions}

Recommended Solution: {recommended}

=== YOUR TASK ===
Create a safe, production-ready remediation plan. Prioritize:
1. Immediate stability (stop the bleeding)
2. Root cause fix
3. Verification

Return this exact JSON:
{{
  "final_solution": "One paragraph describing the chosen solution and why it's safest.",
  "pre_checks": [
    "Pre-check 1: verify X before starting",
    "Pre-check 2: confirm Y",
    "Pre-check 3: ensure Z"
  ],
  "steps": [
    {{
      "step_number": 1,
      "action": "What to do",
      "command": "exact shell command if applicable, or null",
      "expected_outcome": "What success looks like"
    }},
    {{
      "step_number": 2,
      "action": "What to do",
      "command": "exact shell command or null",
      "expected_outcome": "What success looks like"
    }}
  ],
  "post_checks": [
    "Post-check 1",
    "Post-check 2",
    "Post-check 3"
  ],
  "rollback": [
    "Rollback step 1: how to undo if this makes things worse",
    "Rollback step 2",
    "Rollback step 3"
  ],
  "estimated_downtime": "X minutes",
  "severity": "CRITICAL or HIGH or MEDIUM"
}}

Include at least 6 concrete remediation steps. Commands must be real and executable.
"""


def _format_solutions(research: ResearchOutput) -> str:
    parts = []
    for i, s in enumerate(research.solutions, 1):
        parts.append(
            f"Solution {i}: {s.title}\n"
            f"Steps: {s.steps}\n"
            f"Pros: {s.pros}\n"
            f"Cons: {s.cons}\n"
            f"Source: {s.source}"
        )
    return "\n\n".join(parts)


def run(agent1_output: LogAnalysisOutput, agent2_output: ResearchOutput) -> PlannerOutput:
    """
    Args:
        agent1_output: Output from Log Analysis Agent
        agent2_output: Output from Solution Research Agent
    Returns:
        PlannerOutput
    """
    evidence_text = "\n".join(f"  - {e}" for e in agent1_output.evidence)
    solutions_text = _format_solutions(agent2_output)

    prompt = PLANNER_PROMPT.format(
        root_cause=agent1_output.suspected_root_cause,
        confidence=agent1_output.confidence,
        affected_endpoints=", ".join(agent1_output.affected_endpoints),
        evidence=evidence_text,
        timeline=agent1_output.timeline_summary,
        solutions=solutions_text,
        recommended=agent2_output.recommended,
    )

    result = call_llm_json(prompt)

    # Convert steps list to RemediationStep objects
    raw_steps = result.get("steps", [])
    steps = []
    for s in raw_steps:
        steps.append(RemediationStep(
            step_number=s.get("step_number", len(steps) + 1),
            action=s.get("action", ""),
            command=s.get("command"),
            expected_outcome=s.get("expected_outcome", ""),
        ))
    result["steps"] = [s.model_dump() for s in steps]

    return PlannerOutput(**result)


if __name__ == "__main__":
    import json
    from models.schemas import LogAnalysisOutput, ResearchOutput, Solution

    a1 = LogAnalysisOutput(
        suspected_root_cause="SQLAlchemy QueuePool exhausted due to session leak in rebalance_service.py",
        evidence=["QueuePool limit of size 20 overflow 5 reached, connection timed out"],
        confidence=0.92,
        alternate_hypotheses=["PostgreSQL max_connections too low"],
        affected_endpoints=["/api/v1/portfolio/summary", "/api/v1/orders/rebalance"],
        timeline_summary="Pool exhausted at 11:41. Workers crashed by 11:42.",
    )
    a2 = ResearchOutput(
        solutions=[
            Solution(
                title="Fix DB Session Leak",
                steps="Step 1: Add context manager\nStep 2: Deploy fix",
                pros="Permanent fix",
                cons="Requires deployment",
                source="https://docs.sqlalchemy.org/en/20/core/pooling.html",
            )
        ],
        recommended="Fix DB Session Leak: addresses root cause.",
        search_queries_used=["SQLAlchemy QueuePool exhausted fix"],
    )
    out = run(a1, a2)
    print(json.dumps(out.model_dump(), indent=2))
