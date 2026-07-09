"""Streamlit demo UI for the Enterprise Multi-Agent Loan Approval prototype.

Pick a sample applicant -> Run Pipeline -> watch each agent's output land
-> see the final decision -> if escalated, act as the human underwriter
yourself. Every step is logged to SQLite (db/loan_mas.db) exactly like
the audit trail described in the design report (S9.5).
"""
import streamlit as st
import pandas as pd

from db import db
from graph.build_graph import build_graph
from mock_data.sample_applications import SAMPLE_APPLICATIONS

st.set_page_config(page_title="Loan Approval MAS — Prototype", layout="wide")
db.init_db()

AGENT_ORDER = ["doc_verification", "credit_assessment", "risk_assessment", "loan_decision", "human_review"]
AGENT_LABELS = {
    "doc_verification": "📄 Document Verification",
    "credit_assessment": "💳 Credit Assessment",
    "risk_assessment": "📊 Risk Assessment",
    "loan_decision": "⚖️ Loan Decision",
    "human_review": "🧑‍⚖️ Human Review",
}


def confidence_badge(conf):
    if conf is None:
        return "⏳ pending"
    if conf >= 0.75:
        return f"🟢 {conf:.2f}"
    if conf >= 0.5:
        return f"🟡 {conf:.2f}"
    return f"🔴 {conf:.2f}"


def render_waiting(box, agent_name):
    with box.container(border=True):
        st.markdown(f"**{AGENT_LABELS[agent_name]}**")
        st.caption("waiting…")


def render_running(box, agent_name):
    with box.container(border=True):
        st.markdown(f"**{AGENT_LABELS[agent_name]}**")
        st.markdown("🔄 running on your local Ollama model…")


def render_skipped(box, agent_name):
    with box.container(border=True):
        st.markdown(f"**{AGENT_LABELS[agent_name]}**")
        st.caption("not needed — decision was auto-resolved without escalation")


def render_done(box, entry):
    with box.container(border=True):
        st.markdown(f"**{AGENT_LABELS[entry['agent']]}** — {confidence_badge(entry['confidence'])} · `{entry['status']}`")
        st.json(entry["output"], expanded=False)


def run_pipeline_streaming(app_id: str, placeholders: dict):
    """Drives the graph with .stream() instead of .invoke() so each
    agent's panel updates the moment that agent finishes, instead of
    everything landing at once at the end."""
    sample = SAMPLE_APPLICATIONS[app_id]
    applicant = sample["applicant"]
    db.log_application(app_id, applicant["full_name"], applicant["product_type"], applicant["requested_amount"])

    graph = build_graph()
    initial_state = {
        "application_id": app_id,
        "applicant": applicant,
        "documents": sample["documents"],
        "hard_stop_flags": [],
        "escalated": False,
        "trace": [],
    }

    render_running(placeholders[AGENT_ORDER[0]], AGENT_ORDER[0])

    rendered = 0
    final_state = initial_state
    for state_chunk in graph.stream(initial_state, stream_mode="values"):
        final_state = state_chunk
        trace = state_chunk.get("trace", [])
        for entry in trace[rendered:]:
            render_done(placeholders[entry["agent"]], entry)
            if entry["agent"] != "human_review":
                db.log_agent_run(app_id, entry["agent"], entry["output"], entry["confidence"],
                                  entry["model_name"], entry["status"])
            next_idx = AGENT_ORDER.index(entry["agent"]) + 1
            if next_idx < len(AGENT_ORDER) - 1:  # don't pre-mark human_review as running -- it's conditional
                render_running(placeholders[AGENT_ORDER[next_idx]], AGENT_ORDER[next_idx])
        rendered = len(trace)

    if not final_state.get("escalated"):
        render_skipped(placeholders["human_review"], "human_review")

    decision = final_state.get("decision")
    if decision:
        db.log_decision(app_id, decision["outcome"], {"policy_flags": decision.get("policy_flags", [])},
                         final_state.get("decision_confidence"), decision["rationale"],
                         escalated=final_state.get("escalated", False))

    return final_state


st.title("Enterprise Multi-Agent Loan Approval — Prototype")
st.caption("Free / local stack: Ollama (llama3.2:3b) + LangGraph + SQLite. Companion to the design report.")

tab_run, tab_audit = st.tabs(["Run a pipeline", "Audit log"])

with tab_run:
    col_pick, col_info = st.columns([1, 2])
    with col_pick:
        app_id = st.selectbox("Sample application", list(SAMPLE_APPLICATIONS.keys()))
        run_clicked = st.button("▶ Run Pipeline", type="primary")
    with col_info:
        a = SAMPLE_APPLICATIONS[app_id]["applicant"]
        st.markdown(
            f"**{a['full_name']}** · {a['employer_name']} · requesting "
            f"**₹{a['requested_amount']:,}** over {a['tenure_months']} months"
        )

    if run_clicked:
        st.divider()
        st.subheader("Agent trace — live")
        placeholders = {}
        for agent_name in AGENT_ORDER:
            box = st.empty()
            render_waiting(box, agent_name)
            placeholders[agent_name] = box

        st.session_state["result"] = run_pipeline_streaming(app_id, placeholders)
        st.session_state["result_app_id"] = app_id
        st.rerun()

    result = st.session_state.get("result")

    if result and st.session_state.get("result_app_id") == app_id:
        st.divider()
        st.subheader("Agent trace")
        for agent_name in AGENT_ORDER:
            box = st.empty()
            entry = next((e for e in result.get("trace", []) if e["agent"] == agent_name), None)
            if entry:
                render_done(box, entry)
            else:
                render_skipped(box, agent_name)

        st.divider()
        decision = result.get("decision")
        if decision:
            st.subheader("Decision")
            c1, c2, c3 = st.columns(3)
            c1.metric("Outcome", decision["outcome"].upper())
            c2.metric("Confidence", f"{result.get('decision_confidence', 0):.2f}")
            c3.metric("Escalated?", "Yes" if result.get("escalated") else "No")
            st.write(decision["rationale"])
            if decision.get("policy_flags"):
                st.warning(f"Policy flags: {', '.join(decision['policy_flags'])}")

        if result.get("escalated"):
            st.divider()
            st.subheader("🧑‍⚖️ Human Review — this case was escalated to you")
            with st.form("human_review_form"):
                reviewer = st.text_input("Your name")
                verdict = st.selectbox("Verdict", ["approve", "reject"])
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Submit verdict")
            if submitted:
                db.log_human_review(app_id, reviewer or "anonymous", verdict, notes)
                st.success(f"Verdict recorded: {verdict}. This becomes ground truth for the eval set (report S11.4).")

with tab_audit:
    st.subheader("Applications")
    apps = db.fetch_applications()
    if apps:
        st.dataframe(pd.DataFrame(apps), use_container_width=True)
    else:
        st.info("No applications run yet.")

    st.subheader("Audit log")
    filter_id = st.text_input("Filter by application ID (optional)")
    log = db.fetch_audit_log(filter_id or None)
    if log:
        st.dataframe(pd.DataFrame(log), use_container_width=True)
    else:
        st.info("No audit events yet.")
