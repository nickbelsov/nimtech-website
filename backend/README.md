# NimTech lead intake — backend foundation (NOT deployed)

Cloudflare Worker + D1 intake for forms from nimtech.ru, bamboo.nimtech.ru, calc.nimtech.ru.

## Current scope
- POST /v1/leads accepts name, phone, consent, form_id, source, page_url, landing_url, referrer, client_id, utm, details.
- Validates basic fields and browser Origin, stores in D1 before CRM delivery.
- Cron retries failed amoCRM delivery. Health endpoint GET /health.
- amoCRM integration is a first-pass prototype: it creates a contact, lead and note. **Before production, implement phone deduplication, durable stage-by-stage delivery, token refresh and CRM field mapping.** Origin is not authentication or bot protection.
- **No MySklad order creation yet.** Must require validated item IDs, quantities, customer identity, organization, warehouse, tax and server-side prices. Never trust totals submitted from a browser.

## Setup checklist
1. Choose a hosting location compliant with applicable personal-data requirements. Do not deploy a personal-data database to a foreign region without checking Russian personal-data localization and cross-border-transfer requirements.
2. Create a D1 database; replace database_id in wrangler.toml; apply schema.sql.
3. Configure AMO_ACCESS_TOKEN and AMO_BASE_URL as Worker secrets. Never put API keys in frontend or GitHub.
4. Add anti-bot controls, per-IP rate limiting, a data retention/deletion policy, and monitoring.
5. Configure a stable api subdomain, HTTPS and CORS.
6. Run an end-to-end test in a test CRM pipeline; verify duplicates and failure recovery.
7. Only then switch frontend from mailto to POST /v1/leads.

## Future orders API
POST /v1/order-drafts should accept a validated calculator project and line items. It should create a draft/customer order in MySklad after explicit user confirmation or a configured workflow decision, with idempotency, stock checks and an amoCRM deal link.

## Payload example
{
  "name":"Тест",
  "phone":"+79990000000",
  "consent":true,
  "form_id":"homepage_calculator",
  "source":"website",
  "page_url":"https://nimtech.ru/",
  "landing_url":"https://nimtech.ru/?utm_source=...",
  "referrer":"",
  "client_id":"...",
  "utm":{"utm_source":"yandex","utm_medium":"cpc","utm_campaign":"terrace"},
  "details":{"calculator_project_id":null}
}
