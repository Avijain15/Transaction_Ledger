from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import AccountCreate, AccountOut, BalanceOut
from app.services.account_service import create_account, get_account, parse_account_id


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountOut, status_code=201)
def post_account(body: AccountCreate, session: Session = Depends(get_session)) -> AccountOut:
    account = create_account(session, body.name)
    return AccountOut.model_validate(account, from_attributes=True)


@router.get("/{account_id}/balance", response_model=BalanceOut)
def account_balance(
    account_id: str, session: Session = Depends(get_session)
) -> BalanceOut:
    account = get_account(session, account_id)
    return BalanceOut(account_id=parse_account_id(account_id), balance=account.balance)
