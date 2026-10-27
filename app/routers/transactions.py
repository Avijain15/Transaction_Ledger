from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import TransactionCreate, TransactionHistoryOut, TransactionOut
from app.services.transaction_service import add_transaction, get_history


router = APIRouter(tags=["transactions"])


@router.post(
    "/accounts/{account_id}/transactions", response_model=TransactionOut, status_code=201
)
def post_transaction(
    account_id: str,
    body: TransactionCreate,
    session: Session = Depends(get_session),
) -> TransactionOut:
    transaction = add_transaction(session, account_id, body)
    return TransactionOut.model_validate(transaction, from_attributes=True)


@router.get("/accounts/{account_id}/transactions", response_model=TransactionHistoryOut)
def transaction_history(
    account_id: str,
    type: str | None = Query(default=None),
    page: str = Query(default="1"),
    limit: str = Query(default="10"),
    session: Session = Depends(get_session),
) -> TransactionHistoryOut:
    return TransactionHistoryOut.model_validate(
        get_history(session, account_id, type, page, limit)
    )
