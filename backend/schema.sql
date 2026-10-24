CREATE TABLE IF NOT EXISTS leads (
 id TEXT PRIMARY KEY,
 idempotency_key TEXT NOT NULL UNIQUE,
 payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0,
 amo_lead_id INTEGER,
 amo_contact_id INTEGER,
 last_error TEXT,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status,created_at);
-- Order requests require separate server-side product/price validation before creating MySklad customer orders.
