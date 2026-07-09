# Loan Approval MAS — Prototype

Free, local, no-cost companion prototype to the design report. Six agents
(Orchestrator via LangGraph + 5 workers), served on a local Ollama model,
persisted to SQLite, demoed through Streamlit.

## Setup

```bash
cd E:\QK\loan-mas-prototype
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Ollama must be running with a model pulled (already set up on this machine):

```bash
ollama pull llama3.2:3b
```

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501. Pick a sample application, click **Run
Pipeline**, watch each agent's output land, see the final decision. If
the case escalates (confidence < 0.75 or a policy flag), fill in the
Human Review panel yourself.

## What's simplified vs. the production design (report S12–13)

| Production design | Prototype |
|---|---|
| Postgres | SQLite (`db/loan_mas.db`) |
| Kafka event bus | In-process LangGraph state |
| OPA policy engine | Plain Python rules (`guardrails/checks.py`) |
| Presidio / Llama Guard | Regex PII redaction (demo-grade) |
| Real OCR pipeline | Mock "OCR'd" text (`mock_data/sample_applications.py`) |
| Real bureau / employer APIs | Deterministic fake lookups (`mock_data/`) |
| Kubernetes, microservices | One Python process |

Same agent boundaries, same state shape, same guardrail philosophy
(schema-validate → retry once → escalate) — just without the
infrastructure a single-machine demo doesn't need.

## Files

```
app.py                       Streamlit UI
graph/state.py                Shared LoanState
graph/build_graph.py          LangGraph wiring (Fig. 3)
graph/nodes/*.py               The 5 worker agents
guardrails/checks.py          Pydantic schemas + guarded LLM call + policy rules
mock_data/*.py                 Sample applicants, fake bureau, fake employer registry
db/schema.sql, db/db.py       SQLite persistence + audit log
```
