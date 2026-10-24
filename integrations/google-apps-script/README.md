# Google Sheets → amoCRM integration

Spreadsheet: https://docs.google.com/spreadsheets/d/1SFTZtcXeIYHFPiJV7W_881dkY7FQrOvwaFxwL61DKOw/edit

Verified amoCRM pipeline **ОБЪЕКТЫ** ID 9611890; initial stage **НОВАЯ ЗАЯВКА** ID 76760446.

## Setup (not deployed)
1. Open spreadsheet → Extensions → Apps Script.
2. Paste Code.gs into the bound Apps Script project.
3. Project Settings → Script properties: set AMO_ACCESS_TOKEN and optionally AMO_BASE_URL. Never put credentials in sheet cells or GitHub.
4. Run setup() once to create a 5-minute trigger; approve scopes.
5. Deploy → New deployment → Web app. Execute as owner. Access settings require a security/privacy decision. **A public Apps Script URL alone is not a secure intake endpoint**: there is no secret in public browser code, and Origin is not verified by Apps Script. Use a same-origin protected relay or CAPTCHA/anti-abuse layer in production.
6. Only after deployment, connect the site form and test end-to-end with consent and a test record.
7. Add alerting and token refresh. Current code is a starter implementation, not a hardened production system.

## Fields
The spreadsheet stores request ID, timestamp, contact details, form/category, source, 5 UTM fields, page/landing/referrer, client IDs, consent timestamp, tags, pipeline, CRM delivery status/IDs, MySklad placeholders and calculator JSON.

## CRM behavior
Find contact by phone, create contact if missing, create lead in pipeline 9611890 and status 76760446, add tags, UTM tracking fields and note. Retry failures every five minutes (up to 8 attempts). Existing contact is reused, while every distinct request creates a lead. Reconciliation of ambiguous API timeouts and note duplicates must be implemented before production.

## Order creation
MySklad is **not** connected. Orders must only be created from a verified project with authoritative product IDs, quantities, server-side prices and explicit business rules, not arbitrary browser data.

## Privacy
Google Sheets may not meet Russian personal-data localization obligations as the primary personal-data store. Verify compliance before collecting live leads.
