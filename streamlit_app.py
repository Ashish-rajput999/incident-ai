"""
streamlit_app.py — AI Incident Response Dashboard

Run: streamlit run streamlit_app.py
"""

import sys
import os
import json
import time
import io

import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IncidentAI · Response System",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root theme ── */
:root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #181b22;
    --border: #232733;
    --accent: #e05c5c;
    --accent2: #5c8ee0;
    --accent3: #5ce088;
    --text: #d4d8e8;
    --muted: #6b7280;
    --mono: 'JetBrains Mono', monospace;
    --sans: 'DM Sans', sans-serif;
}

/* Global */
html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.main { background: var(--bg) !important; }
.block-container { padding: 2rem 2.5rem; max-width: 1400px; }

/* Header */
.incident-header {
    display: flex; align-items: center; gap: 1rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.2rem; margin-bottom: 2rem;
}
.incident-header h1 {
    font-family: var(--mono); font-size: 1.6rem; font-weight: 700;
    color: var(--accent); margin: 0; letter-spacing: -0.5px;
}
.incident-header p { color: var(--muted); font-size: 0.85rem; margin: 0; }
.status-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 8px var(--accent);
    animation: pulse 1.8s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Agent cards */
.agent-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}
.agent-label {
    font-family: var(--mono); font-size: 0.7rem; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.5rem;
}
.agent-title {
    font-family: var(--mono); font-size: 1.05rem; font-weight: 700;
    color: var(--text); margin-bottom: 1rem;
}

/* Root cause box */
.rootcause-box {
    background: linear-gradient(135deg, rgba(224,92,92,0.1), rgba(224,92,92,0.05));
    border: 1px solid rgba(224,92,92,0.3); border-radius: 6px;
    padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-family: var(--mono); font-size: 0.9rem; line-height: 1.6;
    color: #f0b4b4;
}

/* Evidence block */
.evidence-item {
    background: var(--surface2); border-left: 3px solid var(--accent2);
    border-radius: 0 4px 4px 0; padding: 0.6rem 0.9rem; margin-bottom: 0.5rem;
    font-family: var(--mono); font-size: 0.78rem; color: #9bb3e0;
    word-break: break-all; line-height: 1.5;
}

/* Confidence bar */
.conf-wrap { margin: 0.8rem 0 1.2rem 0; }
.conf-label {
    font-family: var(--mono); font-size: 0.72rem; color: var(--muted);
    margin-bottom: 0.3rem;
}
.conf-track {
    background: var(--border); border-radius: 99px; height: 6px;
    overflow: hidden; position: relative;
}
.conf-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--accent), #f0a);
    transition: width 1s ease;
}

/* Solution card */
.solution-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}
.solution-title { font-weight: 600; font-size: 0.95rem; color: var(--accent2); margin-bottom: 0.4rem; }
.tag {
    display: inline-block; font-size: 0.68rem; font-family: var(--mono);
    padding: 0.15rem 0.5rem; border-radius: 4px; margin-right: 0.3rem;
}
.tag-pros { background: rgba(92,224,136,0.15); color: var(--accent3); }
.tag-cons { background: rgba(224,92,92,0.15); color: var(--accent); }

/* Step item */
.step-item {
    display: flex; gap: 1rem; align-items: flex-start;
    padding: 0.7rem 0; border-bottom: 1px solid var(--border);
}
.step-num {
    font-family: var(--mono); font-size: 0.75rem; font-weight: 700;
    color: var(--accent); background: rgba(224,92,92,0.12);
    border: 1px solid rgba(224,92,92,0.3); border-radius: 4px;
    padding: 0.15rem 0.5rem; white-space: nowrap; margin-top: 0.1rem;
}
.step-content { flex: 1; }
.step-action { font-weight: 500; font-size: 0.9rem; margin-bottom: 0.25rem; }
.step-cmd {
    background: #0d1117; border: 1px solid var(--border); border-radius: 4px;
    padding: 0.35rem 0.7rem; font-family: var(--mono); font-size: 0.78rem;
    color: #7dd3a8; margin: 0.3rem 0;
}
.step-outcome { font-size: 0.8rem; color: var(--accent3); }

/* Checklist */
.check-item {
    padding: 0.4rem 0; border-bottom: 1px solid var(--border);
    font-size: 0.88rem; display: flex; gap: 0.6rem; align-items: flex-start;
}
.check-icon { color: var(--accent3); font-family: var(--mono); }
.rollback-icon { color: var(--accent); }

/* Metric badges */
.badge {
    display: inline-block; font-family: var(--mono); font-size: 0.72rem;
    padding: 0.2rem 0.65rem; border-radius: 4px; margin-right: 0.4rem;
    font-weight: 600;
}
.badge-critical { background: rgba(224,92,92,0.2); color: var(--accent); border: 1px solid rgba(224,92,92,0.4); }
.badge-high { background: rgba(255,165,0,0.15); color: #ffb347; border: 1px solid rgba(255,165,0,0.3); }
.badge-medium { background: rgba(92,142,224,0.15); color: var(--accent2); border: 1px solid rgba(92,142,224,0.3); }
.badge-info { background: rgba(92,224,136,0.12); color: var(--accent3); border: 1px solid rgba(92,224,136,0.25); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 5px !important;
    font-family: var(--mono) !important; font-weight: 600 !important;
    font-size: 0.85rem !important; letter-spacing: 0.5px !important;
    padding: 0.55rem 1.5rem !important; cursor: pointer !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Upload widget */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 6px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface2) !important;
    font-family: var(--mono) !important; font-size: 0.82rem !important;
    color: var(--text) !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Download button */
.stDownloadButton > button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important; font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="incident-header">
  <div class="status-dot"></div>
  <div>
    <h1>IncidentAI // Response System</h1>
    <p>3-Agent Pipeline · Log Analysis → Research → Remediation Planning</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
         color: #6b7280; letter-spacing: 2px; text-transform: uppercase;
         padding-bottom: 0.5rem; border-bottom: 1px solid #232733; margin-bottom: 1rem;">
    Configuration
    </div>
    """, unsafe_allow_html=True)

    # ── CHANGED: Groq key + model selector ──
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Free key at https://console.groq.com",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    model_choice = st.selectbox(
        "Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        index=0,
    )
    os.environ["GROQ_MODEL"] = model_choice
    # ── END CHANGED ──

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
         color: #6b7280; letter-spacing: 2px; text-transform: uppercase;
         padding-bottom: 0.5rem;">
    Pipeline Agents
    </div>
    """, unsafe_allow_html=True)

    for label, desc in [
        ("🔍 Agent 1", "Log Analysis (Groq)"),
        ("🌐 Agent 2", "Solution Research (Web)"),
        ("🛠 Agent 3", "Remediation Planner (Groq)"),
    ]:
        st.markdown(
            f'<div style="padding: 0.4rem 0; font-size: 0.82rem;">'
            f'<span style="color: #e05c5c; font-family: monospace;">{label}</span> '
            f'<span style="color: #6b7280;">{desc}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Powered by Groq · console.groq.com")  # ── CHANGED


# ── Log Upload / Sample ──────────────────────────────────────────────────────
st.markdown("### 📂 Log Input")

col_up, col_sample = st.columns([3, 1])
with col_up:
    uploaded = st.file_uploader(
        "Upload log files (nginx-access.log, nginx-error.log, app-error.log)",
        type=["log", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

with col_sample:
    use_sample = st.button("⚡ Use Sample Logs")

# ── Map uploaded files ──────────────────────────────────────────────────────
def load_from_uploads(files) -> dict:
    logs = {"nginx_access": "", "nginx_error": "", "app_error": ""}
    for f in files:
        name = f.name.lower()
        content = f.read().decode("utf-8", errors="replace")
        if "access" in name:
            logs["nginx_access"] = content
        elif "nginx" in name and "error" in name:
            logs["nginx_error"] = content
        elif "app" in name:
            logs["app_error"] = content
    return logs


def load_sample_logs() -> dict:
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    logs = {}
    mapping = {
        "nginx_access": "nginx-access.log",
        "nginx_error": "nginx-error.log",
        "app_error": "app-error.log",
    }
    for key, fname in mapping.items():
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            with open(path) as f:
                logs[key] = f.read()
        else:
            logs[key] = ""
    return logs


logs = st.session_state.get("logs")
if use_sample:
    logs = load_sample_logs()
    st.session_state["logs"] = logs
    st.success(f"✓ Loaded sample logs from /data directory")
elif uploaded:
    logs = load_from_uploads(uploaded)
    st.session_state["logs"] = logs
    loaded = [k for k, v in logs.items() if v]
    st.success(f"✓ Loaded: {', '.join(loaded)}")
elif logs:
    st.success(f"✓ Logs loaded in memory.")

# ── Show log previews ───────────────────────────────────────────────────────
if logs:
    with st.expander("📄 Log Previews", expanded=False):
        t1, t2, t3 = st.tabs(["nginx-access.log", "nginx-error.log", "app-error.log"])
        with t1:
            st.code(logs.get("nginx_access", "")[:2000], language="nginx")
        with t2:
            st.code(logs.get("nginx_error", "")[:2000], language="nginx")
        with t3:
            st.code(logs.get("app_error", "")[:2000], language="python")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Run button ──────────────────────────────────────────────────────────────
run_col, _ = st.columns([2, 5])
with run_col:
    run_clicked = st.button("🚀 Run Incident Analysis")

# ── Pipeline execution ──────────────────────────────────────────────────────
if run_clicked:
    if not logs:
        st.error("Please upload logs or click **Use Sample Logs** first.")
        st.stop()

    # ── CHANGED: validate Groq key ──
    if not os.environ.get("GROQ_API_KEY"):
        st.error("Please enter your Groq API Key in the sidebar.")
        st.stop()

    sys.path.insert(0, os.path.dirname(__file__))

    from main import run_pipeline

    report = None
    progress_bar = st.progress(0, text="Initializing pipeline...")
    status_box = st.empty()

    try:
        status_box.info("🔍 **Agent 1**: Analyzing logs with Groq...")  # ── CHANGED
        progress_bar.progress(10, text="Agent 1: Log Analysis running...")

        import agents.log_agent as log_agent
        import agents.research_agent as research_agent
        import agents.planner_agent as planner_agent
        from models.schemas import FinalReport

        with st.spinner("Agent 1 — Log Analysis..."):
            agent1_out = log_agent.run(logs)

        progress_bar.progress(40, text="Agent 2: Solution Research running...")
        status_box.info("🌐 **Agent 2**: Searching the web for solutions...")

        with st.spinner("Agent 2 — Solution Research..."):
            agent2_out = research_agent.run(agent1_out)

        progress_bar.progress(70, text="Agent 3: Remediation Planning running...")
        status_box.info("🛠️ **Agent 3**: Generating remediation plan...")

        with st.spinner("Agent 3 — Resolution Planning..."):
            agent3_out = planner_agent.run(agent1_out, agent2_out)

        progress_bar.progress(100, text="Pipeline complete!")
        status_box.success("✅ Analysis complete!")

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
        st.session_state["report"] = report

    except Exception as e:
        progress_bar.empty()
        status_box.error(f"❌ Pipeline error: {e}")
        st.exception(e)
        st.stop()

# ── Render report from session state ───────────────────────────────────────
if "report" in st.session_state:
    report = st.session_state["report"]
    a1 = report.agent1_output
    a2 = report.agent2_output
    a3 = report.agent3_output

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── AGENT 1 OUTPUT ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="agent-label">Agent 01 / Log Analysis</div>
    <div class="agent-title">🔍 Root Cause & Evidence</div>
    """, unsafe_allow_html=True)

    severity = a3.severity.upper() if a3 else "HIGH"
    badge_class = f"badge-{severity.lower()}" if severity in ("CRITICAL", "HIGH", "MEDIUM") else "badge-high"

    st.markdown(
        f'<span class="badge {badge_class}">{severity}</span>'
        f'<span class="badge badge-info">confidence {a1.confidence:.0%}</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="rootcause-box">⚠ {a1.suspected_root_cause}</div>',
        unsafe_allow_html=True,
    )

    # Confidence bar
    conf_pct = int(a1.confidence * 100)
    color = "#e05c5c" if a1.confidence < 0.6 else "#5ce088"
    st.markdown(f"""
    <div class="conf-wrap">
      <div class="conf-label">Confidence Score — {conf_pct}%</div>
      <div class="conf-track">
        <div class="conf-fill" style="width:{conf_pct}%; background: {color};"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if a1.confidence < 0.6:
        st.warning(f"⚠️ Confidence {a1.confidence:.0%} is below threshold (60%). Review manually.")

    st.markdown("**Evidence Snippets**")
    for ev in a1.evidence:
        st.markdown(f'<div class="evidence-item">▶ {ev}</div>', unsafe_allow_html=True)

    with st.expander("🔬 Alternate Hypotheses & Timeline"):
        for hyp in a1.alternate_hypotheses:
            st.markdown(f"- {hyp}")
        if a1.timeline_summary:
            st.info(f"📅 {a1.timeline_summary}")
        if a1.affected_endpoints:
            st.markdown("**Affected Endpoints:**")
            for ep in a1.affected_endpoints:
                st.code(ep, language=None)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── AGENT 2 OUTPUT ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="agent-label">Agent 02 / Solution Research</div>
    <div class="agent-title">🌐 Solutions Found</div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<span class="badge badge-info">{len(a2.solutions)} solutions</span>'
        f'<span class="badge badge-medium">{len(a2.search_queries_used)} queries</span>',
        unsafe_allow_html=True,
    )

    for i, sol in enumerate(a2.solutions):
        with st.expander(f"Solution {i+1}: {sol.title}", expanded=(i == 0)):
            st.markdown(
                f'<span class="tag tag-pros">✓ {sol.pros}</span>'
                f'<span class="tag tag-cons">✗ {sol.cons}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("**Steps:**")
            st.code(sol.steps, language=None)
            st.markdown(f"🔗 [Source: {sol.source}]({sol.source})")

    st.markdown("**💡 Recommended:**")
    st.success(a2.recommended)

    if a2.search_queries_used:
        with st.expander("🔎 Search Queries Used"):
            for q in a2.search_queries_used:
                st.markdown(f"`{q}`")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── AGENT 3 OUTPUT ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="agent-label">Agent 03 / Resolution Planner</div>
    <div class="agent-title">🛠️ Remediation Plan</div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<span class="badge {badge_class}">{a3.severity}</span>'
        f'<span class="badge badge-info">⏱ {a3.estimated_downtime}</span>',
        unsafe_allow_html=True,
    )

    st.markdown(f"**Final Solution:** {a3.final_solution}")

    col_pre, col_post = st.columns(2)

    with col_pre:
        st.markdown("**Pre-checks**")
        for c in a3.pre_checks:
            st.markdown(
                f'<div class="check-item"><span class="check-icon">○</span>{c}</div>',
                unsafe_allow_html=True,
            )

    with col_post:
        st.markdown("**Post-checks**")
        for c in a3.post_checks:
            st.markdown(
                f'<div class="check-item"><span class="check-icon">✓</span>{c}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("**Remediation Steps**")
    for step in a3.steps:
        action_html = f'<div class="step-action">{step.action}</div>'
        cmd_html = f'<div class="step-cmd">$ {step.command}</div>' if step.command else ""
        outcome_html = f'<div class="step-outcome">→ {step.expected_outcome}</div>'
        st.markdown(f"""
        <div class="step-item">
          <div class="step-num">STEP {step.step_number:02d}</div>
          <div class="step-content">{action_html}{cmd_html}{outcome_html}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("↩ Rollback Plan"):
        for r in a3.rollback:
            st.markdown(
                f'<div class="check-item"><span class="rollback-icon">↩</span>{r}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── FINAL REPORT DOWNLOAD ────────────────────────────────────────────────
    st.markdown("### 📄 Final Report")
    st.markdown(f"""
    | Field | Value |
    |---|---|
    | Root Cause | {report.root_cause[:80]}... |
    | Confidence | {report.confidence:.0%} |
    | Severity | {a3.severity} |
    | Solutions Found | {len(a2.solutions)} |
    | Remediation Steps | {len(a3.steps)} |
    | Estimated Downtime | {a3.estimated_downtime} |
    """)

    report_json = json.dumps(report.model_dump(), indent=2)

    col_j, col_t, _ = st.columns([1, 1, 3])
    with col_j:
        st.download_button(
            "⬇ Download JSON",
            data=report_json,
            file_name="incident_report.json",
            mime="application/json",
        )
    with col_t:
        lines = [
            "INCIDENT RESPONSE REPORT",
            "=" * 50,
            f"Root Cause: {report.root_cause}",
            f"Confidence: {report.confidence:.0%}",
            f"Severity: {a3.severity}",
            "",
            "EVIDENCE:",
        ] + [f"  - {e}" for e in report.evidence] + [
            "",
            f"RECOMMENDED: {report.recommended_solution}",
            "",
            "REMEDIATION STEPS:",
        ] + [f"  {s.step_number}. {s.action}" + (f"\n     $ {s.command}" if s.command else "")
             for s in a3.steps]
        text_report = "\n".join(lines)
        st.download_button(
            "⬇ Download TXT",
            data=text_report,
            file_name="incident_report.txt",
            mime="text/plain",
        )