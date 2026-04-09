"""
main.py — Orchestrator for the 3-agent incident response pipeline.

Usage:
    python main.py
    python main.py --logs-dir /path/to/logs
"""

import argparse
import json
import os
import sys
import time

from config import LOG_FILES, CONFIDENCE_THRESHOLD
from models.schemas import FinalReport

import agents.log_agent as log_agent
import agents.research_agent as research_agent
import agents.planner_agent as planner_agent


def load_logs(logs_dir: str = None) -> dict[str, str]:
    """Load the three log files. Uses config paths by default."""
    logs = {}
    if logs_dir:
        paths = {
            "nginx_access": os.path.join(logs_dir, "nginx-access.log"),
            "nginx_error": os.path.join(logs_dir, "nginx-error.log"),
            "app_error": os.path.join(logs_dir, "app-error.log"),
        }
    else:
        paths = LOG_FILES

    for key, path in paths.items():
        if not os.path.exists(path):
            print(f"  WARNING: Log file not found: {path}")
            logs[key] = ""
        else:
            with open(path, "r", errors="replace") as f:
                logs[key] = f.read()
            print(f"  Loaded {key}: {len(logs[key])} chars from {path}")

    return logs


def run_pipeline(
    logs: dict[str, str] = None,
    logs_dir: str = None,
    verbose: bool = True,
) -> FinalReport:
    """
    Run the full 3-agent pipeline.

    Args:
        logs: dict with keys nginx_access, nginx_error, app_error (preloaded strings)
        logs_dir: path to directory containing log files (used if logs not provided)
        verbose: print progress to stdout
    Returns:
        FinalReport
    """
    def log(msg):
        if verbose:
            print(msg)

    start = time.time()

    # ── Load logs ──────────────────────────────────────────────────────────
    if logs is None:
        log("\n📂 Loading logs...")
        logs = load_logs(logs_dir)

    # ── Agent 1: Log Analysis ──────────────────────────────────────────────
    log("\n🔍 Running Agent 1: Log Analysis...")
    t0 = time.time()
    agent1_out = log_agent.run(logs)
    log(f"   ✓ Done in {time.time()-t0:.1f}s | confidence={agent1_out.confidence:.2f}")

    if agent1_out.confidence < CONFIDENCE_THRESHOLD:
        log(
            f"   ⚠️  WARNING: Confidence {agent1_out.confidence:.2f} below threshold "
            f"{CONFIDENCE_THRESHOLD}. Results may be unreliable."
        )

    log(f"   Root cause: {agent1_out.suspected_root_cause}")

    # ── Agent 2: Solution Research ─────────────────────────────────────────
    log("\n🌐 Running Agent 2: Solution Research...")
    t0 = time.time()
    agent2_out = research_agent.run(agent1_out)
    log(f"   ✓ Done in {time.time()-t0:.1f}s | found {len(agent2_out.solutions)} solutions")

    # ── Agent 3: Resolution Planner ────────────────────────────────────────
    log("\n🛠️  Running Agent 3: Resolution Planner...")
    t0 = time.time()
    agent3_out = planner_agent.run(agent1_out, agent2_out)
    log(f"   ✓ Done in {time.time()-t0:.1f}s | severity={agent3_out.severity}")

    # ── Assemble Final Report ──────────────────────────────────────────────
    report = FinalReport(
        root_cause=agent1_out.suspected_root_cause,
        evidence=agent1_out.evidence,
        confidence=agent1_out.confidence,
        recommended_solution=agent2_out.recommended,
        remediation_plan=agent3_out,
        agent1_output=agent1_out,
        agent2_output=agent2_out,
        agent3_output=agent3_out,
    )

    log(f"\n✅ Pipeline complete in {time.time()-start:.1f}s")
    return report


def print_report(report: FinalReport):
    """Pretty-print the final incident report."""
    sep = "=" * 70

    print(f"\n{sep}")
    print("  INCIDENT RESPONSE REPORT")
    print(sep)

    print(f"\n🔴 ROOT CAUSE")
    print(f"   {report.root_cause}")
    print(f"   Confidence: {report.confidence:.0%} | Severity: {report.remediation_plan.severity}")

    print(f"\n📋 EVIDENCE")
    for e in report.evidence:
        print(f"   • {e}")

    print(f"\n💡 RECOMMENDED SOLUTION")
    print(f"   {report.recommended_solution}")

    print(f"\n🛠️  REMEDIATION PLAN")
    plan = report.remediation_plan

    print(f"\n   Pre-checks:")
    for c in plan.pre_checks:
        print(f"   ▶ {c}")

    print(f"\n   Steps:")
    for step in plan.steps:
        print(f"\n   [{step.step_number}] {step.action}")
        if step.command:
            print(f"       $ {step.command}")
        print(f"       ✓ {step.expected_outcome}")

    print(f"\n   Post-checks:")
    for c in plan.post_checks:
        print(f"   ▶ {c}")

    print(f"\n   Rollback:")
    for r in plan.rollback:
        print(f"   ↩ {r}")

    print(f"\n   Estimated downtime: {plan.estimated_downtime}")
    print(f"\n{sep}\n")


def main():
    parser = argparse.ArgumentParser(description="AI Incident Response Pipeline")
    parser.add_argument("--logs-dir", default=None, help="Directory containing log files")
    parser.add_argument("--output", default=None, help="Save JSON report to this file")
    args = parser.parse_args()

    try:
        report = run_pipeline(logs_dir=args.logs_dir, verbose=True)
        print_report(report)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report.model_dump(), f, indent=2)
            print(f"📄 Report saved to {args.output}")

    except EnvironmentError as e:
        print(f"\n❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        raise


if __name__ == "__main__":
    main()
