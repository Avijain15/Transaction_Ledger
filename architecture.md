# Architecture — Transaction Ledger API

Source of truth: *Full Stack Developer Assessment.pdf*. Anything the PDF does not specify is listed in §8 as an explicit assumption (the PDF requires an "Assumptions" deliverable).

> PDF notes: section numbering jumps from 5 to 7 (there is no section 6; "Atomicity" sits at the end of section 5). Nothing appears to be missing in content. The history filter line ends with a stray "t." typo.

## 1. Stack (free choice per PDF §10)

| Layer | Choice |
|---|---|
| Language / framework | Python 3.11 + FastAPI |
| Validation | Pydantic |
| DB | PostgreSQL 16 (relational → real constraints, row locks, transactions) |
| Data access | SQLAlchemy 2.0 |
| Frontend (optional, see §11) | Plain HTML + CSS + vanilla JS, served by FastAPI. No build step |
| Run locally | `docker compose up` for DB + `uvicorn app.main:app` (steps go in README) |

## 2. Project structure

```
ledger-api/
├── app/
│   ├── main.py              # app, router registration, exception handlers
│   ├── config.py            # DATABASE_URL
│   ├── db.py                # engine, session, table creation
│   ├── models.py            # Account, Transaction (with constraints)
│   ├── schemas.py           # request/response models
│   ├── errors.py            # AppError + consistent error format
│   ├── routers/             # accounts.py, transactions.py, transfers.py
│   ├── services/            # account_service.py, transaction_service.py, transfer_service.py
│   └── static/              # index.html, styles.css, app.js (frontend, §11)
├── tests/                   # pytest suite (§10)
├── docs/API.md              # API documentation (deliverable)
├── docs/ASSUMPTIONS.md      # copy of §8 (deliverable)
├── docker-compose.yml
├── requirements.txt
└── README.md                # deliverable
```

Layering: **router** (HTTP only) → **service** (business rules + DB transaction) → **models** (constraints).

## 3. Data model

**accounts**

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK (unique) |
| name | VARCHAR | NOT NULL, not blank |
| balance | NUMERIC(14,2) | NOT NULL, DEFAULT 0, CHECK (balance >= 0) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() (system generated) |

**transactions**

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK (unique) |
| account_id | BIGINT | NOT NULL, FK → accounts.id |
| type | VARCHAR | NOT NULL, CHECK IN ('credit','debit') |
| amount | NUMERIC(14,2) | NOT NULL, CHECK (amount > 0) |
| description | TEXT | NOT NULL |
| reference_id | VARCHAR | NOT NULL, **UNIQUE (account_id, reference_id)** |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Index: `(account_id, created_at DESC, id DESC)` for history queries.
Immutability backstop: DB trigger that raises on `UPDATE` / `DELETE` of `transactions`.

## 4. API

| # | Method & path | Purpose | Success |
|---|---|---|---|
| 1 | `POST /accounts` | Create account. Body: `{name}` only | 201 |
| 2 | `POST /accounts/{account_id}/transactions` | Add credit/debit. Body: `{type, amount, description, reference_id}` | 201 |
| 3 | `GET /accounts/{account_id}/balance` | Returns `{account_id, balance}` | 200 |
| 4 | `GET /accounts/{account_id}/transactions?type=&page=&limit=` | History: filter + pagination + latest-first | 200 |
| 5 | `POST /transfers` *(bonus)* | Body: `{from_account_id, to_account_id, amount, description, reference_id}` | 201 |

No `PUT`, `PATCH` or `DELETE` exists for transactions (immutability).

**History response shape**
```json
{
  "data": [ { "id": 1, "account_id": 1, "type": "credit", "amount": "50.00",
              "description": "...", "reference_id": "...", "created_at": "..." } ],
  "pagination": { "page": 1, "limit": 10, "total_records": 25, "total_pages": 3 }
}
```
Sorting: `ORDER BY created_at DESC, id DESC` (id breaks ties).

## 5. Business rules and where each is enforced

| Rule (PDF) | Enforced by |
|---|---|
| Initial balance always 0; client cannot set it | Request schema accepts only `name` and rejects unknown fields; DB default 0 |
| `created_at` system generated | DB default; not in request schemas |
| Credit adds, debit subtracts | Service, inside the DB transaction |
| Debit rejected if balance insufficient; balance unchanged | Service check + `CHECK (balance >= 0)` backstop |
| Duplicate `reference_id` (same account) → no new row, no balance change, "already exists" response | Service pre-check + `UNIQUE (account_id, reference_id)` backstop |
| Same `reference_id` allowed across accounts | Unique key is the pair, not `reference_id` alone |
| Immutability | No mutating endpoints + DB trigger |
| Balance = result of all valid transactions | Balance only changes in the same DB transaction that inserts a transaction row |
| Atomicity | Single DB transaction (insert + balance update); any failure → rollback |
| Concurrency safety | `SELECT … FOR UPDATE` on the account row before reading balance |

## 6. Validation (PDF §7 minimum)

- `name` provided (non-blank)
- `account_id` valid and existing → malformed id = 400, not found = 404
- `type` ∈ {credit, debit}
- `amount` > 0
- `reference_id` provided
- Duplicate `reference_id` handled (409)
- Debit has sufficient balance
- `type`, `page`, `limit` query params validated
- Malformed/invalid body → validation error

## 7. Error handling (PDF §8)

One format for every error:
```json
{ "error": { "code": "INSUFFICIENT_BALANCE", "message": "…", "details": [] } }
```

| Case | HTTP | code |
|---|---|---|
| Invalid request body / amount / type | 400 | `VALIDATION_ERROR` |
| Invalid pagination parameters | 400 | `INVALID_PAGINATION` |
| Invalid account id format | 400 | `INVALID_ACCOUNT_ID` |
| Account not found | 404 | `ACCOUNT_NOT_FOUND` |
| Duplicate transaction | 409 | `DUPLICATE_TRANSACTION` |
| Insufficient balance | 422 | `INSUFFICIENT_BALANCE` |
| Unexpected failure | 500 | `INTERNAL_ERROR` |

## 8. Assumptions (PDF is silent — to be listed in submission)

1. **Stack**: FastAPI + PostgreSQL (PDF allows any).
2. **IDs**: auto-increment integers for accounts and transactions (PDF only says "unique").
3. **Amount**: positive number, max 2 decimal places, stored as `NUMERIC(14,2)`; no currency field (PDF has none).
4. **Description**: required, since the PDF says each transaction "must contain" it.
5. **Extra fields**: unknown fields in a request body (e.g. `balance` on account creation) are rejected, not silently ignored.
6. **Duplicate response**: `409` with `DUPLICATE_TRANSACTION`; the body includes the existing transaction.
7. **Pagination defaults**: `page=1`, `limit=10`, `limit` max 100; `page`/`limit` must be positive integers.
8. **Status codes** in §7 are my choice; the PDF only asks for "proper" codes.
9. **Transfer**: recorded as a debit on the source and a credit on the destination (two ledger rows), so balances always equal the sum of valid transactions. The request carries one `reference_id`, used for both rows. Source = destination is rejected as a validation error.
10. **No authentication**: the PDF does not mention it.
11. **Frontend**: added by request, not required by the PDF (§11). It is a thin client over the same API.

## 9. PDF cross-verification checklist

| PDF section | Covered in |
|---|---|
| 1 Create Account (fields, unique id, name required, balance 0, system `created_at`, no client balance) | §3, §4 #1, §5, §6 |
| 2 Add Transaction (all 7 fields, credit rule, debit rule, insufficient balance, duplicates, same ref across accounts) | §3, §4 #2, §5 |
| 3 Get Balance (`account_id`, `balance`, error if missing) | §4 #3, §7 |
| 4 History (type filter, default both, page/limit, current page / page size / total records / total pages, latest-first) | §4 #4 |
| 5 Data Integrity (immutability, balance consistency, rejected tx has no effect, atomicity) | §3, §5 |
| 7 Validations (all 9 bullets) | §6 |
| 8 Error Handling (all 7 cases) | §7 |
| 9 Bonus Transfer (sufficient balance, both exist, atomic, full rollback, no partial) | §4 #5, §8.9; flow in `flow.md` |
| 10 Technical Requirements (any stack/DB, clean structure, validation, errors, DB constraints, README to run) | §1, §2, §3, §6, §7 |
| 11 Submission (source, README, API docs, assumptions) | §2, §8 |
| *Not in PDF*: testing approach, frontend | §10, §11 |

## 10. How it will be tested

The PDF asks for a runnable backend; it does not specify a test method. Four ways, from fastest to most thorough:

| Method | How | What it proves |
|---|---|---|
| Swagger UI | Open `http://localhost:8000/docs` (auto-generated by FastAPI). Every endpoint can be called from the browser | API works and is self-documenting |
| Frontend | Open `http://localhost:8000/` (§11) | Full flow end to end by clicking |
| curl / Postman | Commands listed in `docs/API.md` | Raw request/response and status codes |
| pytest | `pytest` (runs against a separate test database) | Every PDF rule, repeatable |

**pytest cases (one per PDF rule)**

1. Create account → balance is 0, `created_at` set; body with `balance` → 400; missing/blank `name` → 400
2. Credit 100, credit 50, debit 30, debit 20 → balance 100 (PDF §5 example)
3. Debit 150 on balance 100 → 422, balance stays 100
4. Same `reference_id` twice on one account → 409, one row, balance unchanged
5. Same `reference_id` on two different accounts → both succeed
6. Invalid `type`, amount `0` / negative, missing `reference_id` → 400
7. Unknown account → 404; malformed account id → 400
8. History: filter by `credit` / `debit`, no filter returns both, latest-first order, pagination fields correct, invalid `page`/`limit` → 400
9. `PUT` / `PATCH` / `DELETE` on a transaction → 405; direct SQL `UPDATE`/`DELETE` blocked by trigger
10. Transfer 30 from A(100) to B(50) → A 70, B 80; insufficient balance, unknown account, same account → no balance change on either
11. Atomicity: force a failure after the insert → no row and no balance change
12. Concurrency: parallel debits that together exceed the balance → balance never negative

## 11. Frontend (optional, beyond the PDF)

The PDF describes a **backend API only**; no UI is required. This frontend is an extra, so reviewers can try the API without Postman. It must not change any API behavior.

**Approach**: three static files in `app/static/`, served by FastAPI at `/`. Same origin as the API, so no CORS setup and no build tooling.

**Single page, five cards**

| Card | Uses |
|---|---|
| Create account (name) | `POST /accounts` |
| Account picker + balance (enter account id) | `GET /accounts/{id}/balance` |
| New transaction (credit/debit, amount, description, reference id) | `POST /accounts/{id}/transactions` |
| History: All / Credit / Debit segmented control, newest first, Previous / Next, "Page x of y · n records" | `GET /accounts/{id}/transactions` |
| Transfer (bonus) | `POST /transfers` |

Every API error is shown inline using the `error.message` from §7. Nothing is hidden or retried by the UI.

**Apple-style theme (standard, minimal)**

| Element | Style |
|---|---|
| Font | `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif` |
| Background / cards | `#f5f5f7` page, white cards, 18px radius, soft shadow |
| Accent | `#0071e3` (primary buttons, focus ring) |
| Credit / debit colors | Green `#34c759` / red `#ff3b30` |
| Controls | Pill buttons, 12px-radius inputs, iOS-style segmented control for the filter |
| Layout | Centered column, max-width 720px, generous spacing |
| Dark mode | `prefers-color-scheme: dark` → `#000` page, `#1c1c1e` cards |

**Frontend assumptions**: account id is entered manually after creation (the PDF has no "list accounts" API, so none is added); the UI stores nothing locally.