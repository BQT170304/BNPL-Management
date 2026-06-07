# API Reference

**Base URL (production):** `https://d2ttyqgmp7bw35.cloudfront.net/api`  
**Auth:** `Authorization: Bearer <token>` — obtain via `POST /api/auth/login`, or use static token `demo-token-bnpl`

> All routes are prefixed with `/api`. CloudFront routes `/api/*` → ALB → ECS.

---

## Auth

### POST /auth/login
```json
{ "username": "nguyenvana", "password": "123456" }
→ { "access_token": "...", "token_type": "bearer" }
```

---

## Profiles

### POST /profiles
Create a financial profile.

### GET /profiles/{id}/analysis
Returns NCF, DTI, EFR, PGRS scores + tier + alerts.

### GET /profiles/{id}/forecast?months=6
Monthly cash flow forecast (6 months default).

### GET /profiles/{id}/forecast/daily?days=90
Daily cash flow forecast.

### GET /profiles/{id}/alerts?include_forecast=true
Smart alerts based on analysis + forecast.

### GET /profiles/{id}/obligations
List payment obligations.

### POST /profiles/{id}/obligations
Add an obligation.

### DELETE /profiles/{id}/obligations/{oid}
Remove an obligation.

### POST /profiles/{id}/obligations/from-cif/{cif}
Seed obligations from CIF ingestion data.

---

## Planning

### POST /planning/recommend
Recommend best payment option for a purchase.
```json
{
  "profile_id": "demo-profile",
  "purchase_amount": 5000000,
  "merchant": "Apple",
  "category": "electronics"
}
```

### POST /planning/simulate
Simulate the financial impact of a payment option.

---

## Ingestion (CIF Data)

### GET /ingestion/cifs
List all CIF numbers in the CSV dataset.

### GET /ingestion/cif/{cif}/seed?strategy=latest
Extract financial profile from CIF transaction history.

### GET /ingestion/cif/{cif}/obligation-seeds
List obligations detected from CIF transactions.

---

## Decisions

### GET /decisions/{id}
Get a decision record.

### POST /decisions/{id}/explain
Generate LLM explanation for a decision.

### POST /decisions/{id}/override
Override a decision with reason.

### POST /decisions/{id}/outcomes
Record the actual outcome of a decision.

---

## Feedback & Portfolio

### GET /feedback/metrics
Aggregate model performance metrics.

### GET /feedback/dataset
Export labelled dataset for retraining.

### GET /portfolio/summary
Portfolio-level summary across all profiles.

---

## Copilot

### POST /copilot/chat
```json
{ "message": "Should I buy this phone on BNPL?", "profile_id": "demo-profile" }
→ { "reply": "..." }
```

---

## Consent

### POST /consents
Grant consent.

### GET /consents/{id}
Get consent record.

### POST /consents/{id}/revoke
Revoke consent.

### GET /cifs/{cif}/consents
List consents for a CIF.

---

## Health

### GET /health
```json
{ "status": "ok" }
```
