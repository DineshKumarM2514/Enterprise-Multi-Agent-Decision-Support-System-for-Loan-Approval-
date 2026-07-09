# Enterprise Multi-Agent Decision Support System — Loan Approval

Two parts, one project:

- **[`report/`](report/index.html)** — the design report: architecture, data schema, guardrails, security, MLOps, scaling to 1M applications/year, and the business case. Static HTML, deployed via Vercel.
- **[`prototype/`](prototype/README.md)** — a working, free, self-hosted implementation of the same architecture: six agents (LangGraph orchestrator + five workers) served on a local Ollama model, with a Streamlit UI. See its README for setup and run instructions.
