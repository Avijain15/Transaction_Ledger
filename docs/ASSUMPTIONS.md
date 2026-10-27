# Assumptions

1. **Stack**: FastAPI + PostgreSQL (the assessment allows any stack).
2. **IDs**: auto-increment integers for accounts and transactions (the assessment only says unique).
3. **Amount**: positive number, maximum 2 decimal places, stored as `NUMERIC(14,2)`; no currency field (the assessment has none).
4. **Description**: required, since the assessment says each transaction must contain it.
5. **Extra fields**: unknown request-body fields (for example, `balance` on account creation) are rejected, not silently ignored.
6. **Duplicate response**: HTTP 409 with `DUPLICATE_TRANSACTION`; the error details include the existing transaction.
7. **Pagination defaults**: `page=1`, `limit=10`, `limit` maximum 100; page and limit must be positive integers.
8. **Status codes**: the chosen codes are documented in the architecture; the assessment asks for appropriate codes without prescribing exact ones.
9. **Transfer**: recorded as a debit on the source and a credit on the destination (two ledger rows), so balances equal the sum of valid transactions. The request's one `reference_id` is used for both rows. Transfers from an account to itself are rejected as validation errors.
10. **Authentication**: none, because the assessment does not mention it.
11. **Frontend**: a thin same-origin client over the API, served by FastAPI. Account IDs are entered manually because the assessment has no account-list endpoint; the UI stores no account state locally.
