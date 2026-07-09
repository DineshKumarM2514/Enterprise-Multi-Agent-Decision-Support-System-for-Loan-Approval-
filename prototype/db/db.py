"""SQLite persistence layer. Stands in for Postgres in the production design
(report S6.4) -- same table shapes, zero setup.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).parent / "loan_mas.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def log_application(app_id: str, name: str, product_type: str, amount: float) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO applications (id, applicant_name, product_type, requested_amount, status, created_at) "
        "VALUES (?, ?, ?, ?, 'intake', ?)",
        (app_id, name, product_type, amount, _now()),
    )
    conn.commit()
    conn.close()
    log_audit(app_id, "application.intake", "orchestrator", {"name": name, "amount": amount})


def log_agent_run(app_id: str, agent_name: str, output: dict, confidence: Optional[float],
                   model_name: str, status: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO agent_runs (application_id, agent_name, output_json, confidence, model_name, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (app_id, agent_name, json.dumps(output), confidence, model_name, status, _now()),
    )
    conn.commit()
    conn.close()
    log_audit(app_id, f"agent.{agent_name}.completed", agent_name,
              {"confidence": confidence, "status": status})


def log_decision(app_id: str, outcome: str, terms: dict, confidence: Optional[float], rationale: str,
                  escalated: bool = False) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO decisions (application_id, outcome, terms_json, decision_confidence, rationale, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (app_id, outcome, json.dumps(terms), confidence, rationale, _now()),
    )
    # The agent's recommended outcome is preserved above for the audit trail;
    # the application's headline status only becomes final once a human has
    # signed off on an escalated case (see log_human_review).
    status = "pending_human_review" if escalated else outcome
    conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    conn.commit()
    conn.close()
    log_audit(app_id, "decision.recorded", "loan_decision",
              {"recommended_outcome": outcome, "confidence": confidence, "escalated": escalated})


def log_human_review(app_id: str, reviewer: str, verdict: str, notes: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO human_reviews (application_id, reviewer_name, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?)",
        (app_id, reviewer, verdict, notes, _now()),
    )
    conn.execute("UPDATE applications SET status = ? WHERE id = ?", (f"human_{verdict}", app_id))
    conn.commit()
    conn.close()
    log_audit(app_id, "human_review.recorded", reviewer, {"verdict": verdict})


def log_audit(app_id: str, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_log (application_id, event_type, actor, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (app_id, event_type, actor, json.dumps(payload), _now()),
    )
    conn.commit()
    conn.close()


def fetch_audit_log(app_id: Optional[str] = None):
    conn = get_conn()
    if app_id:
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE application_id = ? ORDER BY id DESC", (app_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_applications():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
