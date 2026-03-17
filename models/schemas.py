from pydantic import BaseModel, Field
from typing import List, Optional


class LogAnalysisOutput(BaseModel):
    suspected_root_cause: str
    evidence: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    alternate_hypotheses: List[str]
    affected_endpoints: List[str] = []
    timeline_summary: str = ""


class Solution(BaseModel):
    title: str
    steps: str
    pros: str
    cons: str
    source: str


class ResearchOutput(BaseModel):
    solutions: List[Solution]
    recommended: str
    search_queries_used: List[str] = []


class RemediationStep(BaseModel):
    step_number: int
    action: str
    command: Optional[str] = None
    expected_outcome: str


class PlannerOutput(BaseModel):
    final_solution: str
    pre_checks: List[str]
    steps: List[RemediationStep]
    post_checks: List[str]
    rollback: List[str]
    estimated_downtime: str = "0 minutes"
    severity: str = "HIGH"


class FinalReport(BaseModel):
    root_cause: str
    evidence: List[str]
    confidence: float
    recommended_solution: str
    remediation_plan: PlannerOutput
    agent1_output: LogAnalysisOutput
    agent2_output: ResearchOutput
    agent3_output: PlannerOutput
