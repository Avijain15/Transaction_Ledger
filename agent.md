# agent.md

## Status
| Phase | Status (todo / doing / done) | Notes |
|---|---|---|
| 0 | done | Read `Full Stack Developer Assessment.pdf`, `architecture.md`, and `flow.md` fully. |
| 1 | done | Added specified package structure, pinned dependencies, PostgreSQL 16 compose service, config, and gitignore. |
| 2 | done | Added account and transaction models, constraints/index, and idempotent table/immutability-trigger creation. |
| 3 | done | Added extra-field rejection, typed transaction requests/responses, money serialization, AppError/error envelope primitives. |
| 4 | done | Added POST account creation with zero balance and GET balance with id/not-found validation. |
| 5 | done | Added locked atomic transaction writes, duplicate detail payload, debit checks, and latest-first filtered pagination. |
| 6 | done | Added two-row transfers with ascending account locks, duplicate checks, sufficient-balance validation, and atomic updates. |
| 7 | done | Added FastAPI startup, routers, unified error envelope, and the five-card frontend served at `/`; Swagger UI is at `/docs`. |
| 8 | done | All 12 PostgreSQL-backed tests passed during verification; the test suite was removed from the submission per the user's cleanup request. |
| 9 | done | Added README local/test instructions, complete endpoint docs with curl examples, and documented assumptions. |
| 10 | done | Rechecked source, docs, runtime routes, frontend assets, and the full PostgreSQL suite. |

## Decisions
- Followed architecture section 8 assumptions for unspecified implementation details. The PDF makes transfer a bonus; implementing it in Phase 6 as requested by the implementation prompt.
- UI: implement the five-card frontend described in architecture section 11, following the user's latest instruction.
- Final cleanup: remove the automated test suite, its README instructions, and its test-only dependencies after all 12 tests passed.

## Deviations/Blockers
- The required PDF is at `D:\Full Stack Developer Assessment.pdf`, outside the repository root; it was accessible and read in full.
- Cleanup note: source tests and test-only dependencies are removed, and `ledger_test` is empty. The ignored `tests/__pycache__` folder remains because the workspace sandbox rejected its deletion; remove it locally before packaging.

## Architecture section 9 checklist
| Checklist item | Status | Evidence |
|---|---|---|
| PDF section 1: account fields, zero opening balance, generated timestamp | checked | `POST /accounts`, account model defaults/constraints, account tests authored |
| PDF section 2: credit/debit, insufficient balance, duplicate references and account-scoped uniqueness | checked | Transaction service/model and tests authored |
| PDF section 3: balance lookup and missing account | checked | Balance route/service and tests authored |
| PDF section 4: type filter, pagination metadata, latest-first ordering | checked | History service and tests authored |
| PDF section 5: immutable ledger, balance consistency, rejected writes, atomicity | checked | PostgreSQL trigger, one-transaction service logic, and tests authored |
| PDF section 7: request, ID, type, amount, duplicate, and balance validation | checked | Pydantic contracts, service checks, and tests authored |
| PDF section 8: consistent errors and appropriate status codes | checked | Shared error envelope and global handlers; route checks passed |
| PDF section 9: atomic money transfer | checked | Transfer service and tests authored |
| PDF section 10: maintainable stack, validation, errors, DB constraints, local run | checked | Project structure, database models, README, and compose config |
| PDF section 11: source, README, API documentation, assumptions | checked | Deliverables present |
| Test approach | checked | All 12 PostgreSQL tests passed before the suite was removed per the final cleanup request |
| Optional frontend | implemented | Five cards call the account, balance, transaction, history, and transfer API operations |

## Last verification (date, command, result)
- 2026-10-27 - `.venv\Scripts\python -m pytest tests -q -p no:cacheprovider` passed all 12 PostgreSQL tests before the test files were removed per the final cleanup request. Python compilation, frontend page/assets, `/docs`, `/openapi.json`, all five API operation paths, validation envelopes, duplicate details, JavaScript syntax, and `docker compose config` passed. Test database rows were verified empty after cleanup.
