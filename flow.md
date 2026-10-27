# Flow — Transaction Ledger API

Every write runs inside **one DB transaction**. Any error → rollback → nothing persisted.

## 1. Create Account — `POST /accounts`

1. Validate body: only `name`, non-blank. Unknown fields (e.g. `balance`) → 400.
2. Insert account (`balance = 0`, `created_at` set by DB).
3. Return 201 with `id, name, balance, created_at`.

## 2. Add Transaction — `POST /accounts/{account_id}/transactions`

```mermaid
flowchart TD
    A[Request] --> B{account_id valid format?}
    B -- no --> E1[400 INVALID_ACCOUNT_ID]
    B -- yes --> C{Body valid?<br/>type, amount > 0,<br/>description, reference_id}
    C -- no --> E2[400 VALIDATION_ERROR]
    C -- yes --> D[BEGIN; lock account row FOR UPDATE]
    D --> F{Account exists?}
    F -- no --> E3[404 ACCOUNT_NOT_FOUND]
    F -- yes --> G{reference_id already used<br/>for this account?}
    G -- yes --> E4[409 DUPLICATE_TRANSACTION<br/>no insert, balance unchanged]
    G -- no --> H{type = debit AND<br/>balance < amount?}
    H -- yes --> E5[422 INSUFFICIENT_BALANCE<br/>balance unchanged]
    H -- no --> I[Insert transaction row]
    I --> J[Update balance: credit +amount / debit -amount]
    J --> K[COMMIT]
    K --> L[201 Created]
```

Any failure between BEGIN and COMMIT → ROLLBACK (neither the row nor the balance change is saved).

## 3. Get Balance — `GET /accounts/{account_id}/balance`

1. Validate id format → 400 if invalid.
2. Look up account → 404 if missing.
3. Return `{ account_id, balance }`.

## 4. Get Transaction History — `GET /accounts/{account_id}/transactions?type=&page=&limit=`

1. Validate id format (400) and `type` ∈ {credit, debit} if given (400).
2. Validate `page` and `limit` (positive integers, limit ≤ 100; defaults 1 / 10) → 400 if invalid.
3. Account exists? → 404 if not.
4. Query the account's transactions, apply `type` filter if present, `ORDER BY created_at DESC, id DESC`, apply `LIMIT/OFFSET`.
5. Count total records for the same filter → `total_pages = ceil(total_records / limit)`.
6. Return `{ data: [...], pagination: { page, limit, total_records, total_pages } }`.

## 5. Transfer (Bonus) — `POST /transfers`

```mermaid
flowchart TD
    A[Request: from, to, amount, description, reference_id] --> B{Body valid?<br/>amount > 0, from != to}
    B -- no --> E1[400 VALIDATION_ERROR]
    B -- yes --> C[BEGIN; lock both account rows<br/>FOR UPDATE in ascending id order]
    C --> D{Both accounts exist?}
    D -- no --> E2[404 ACCOUNT_NOT_FOUND]
    D -- yes --> F{reference_id already used<br/>on either account?}
    F -- yes --> E3[409 DUPLICATE_TRANSACTION]
    F -- no --> G{Source balance >= amount?}
    G -- no --> E4[422 INSUFFICIENT_BALANCE]
    G -- yes --> H[Insert debit row on source]
    H --> I[Insert credit row on destination]
    I --> J[Update both balances]
    J --> K[COMMIT]
    K --> L[201 Created]
```

Any failure → ROLLBACK of the whole transfer. A partial transfer cannot be persisted.

## 6. Immutability

There are no `PUT`, `PATCH` or `DELETE` routes for transactions. A DB trigger also rejects `UPDATE`/`DELETE` on the `transactions` table.
