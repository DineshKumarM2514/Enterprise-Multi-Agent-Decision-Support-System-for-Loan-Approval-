-- Simplified from the design report's ERD (S6.2), adapted for SQLite.
-- Every agent writes its own append-only row -- nothing is ever updated in place.

CREATE TABLE IF NOT EXISTS applications (
    id                TEXT PRIMARY KEY,
    applicant_name    TEXT NOT NULL,
    product_type      TEXT NOT NULL,
    requested_amount  REAL NOT NULL,
    status            TEXT NOT NULL DEFAULT 'intake',
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id    TEXT NOT NULL,
    agent_name        TEXT NOT NULL,
    output_json       TEXT NOT NULL,
    confidence        REAL,
    model_name        TEXT NOT NULL,
    status            TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id       TEXT NOT NULL,
    outcome              TEXT NOT NULL,
    terms_json           TEXT,
    decision_confidence  REAL,
    rationale            TEXT,
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_reviews (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id    TEXT NOT NULL,
    reviewer_name     TEXT,
    verdict           TEXT,
    notes             TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id    TEXT NOT NULL,
    event_type        TEXT NOT NULL,
    actor             TEXT NOT NULL,
    payload_json      TEXT,
    created_at        TEXT NOT NULL
);
