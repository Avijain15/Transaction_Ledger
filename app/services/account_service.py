from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Account


def parse_account_id(raw_account_id: str) -> int:
    try:
        account_id = int(raw_account_id)
    except ValueError as exc:
        raise AppError(400, "INVALID_ACCOUNT_ID", "Account id must be an integer") from exc
    if account_id <= 0 or account_id > 9_223_372_036_854_775_807:
        raise AppError(400, "INVALID_ACCOUNT_ID", "Account id must be a valid positive integer")
    return account_id


def create_account(session: Session, name: str) -> Account:
    with session.begin():
        account = Account(name=name, balance=Decimal("0.00"))
        session.add(account)
        session.flush()
        session.refresh(account)
    return account


def get_account(session: Session, raw_account_id: str) -> Account:
    account_id = parse_account_id(raw_account_id)
    account = session.scalar(select(Account).where(Account.id == account_id))
    if account is None:
        raise AppError(404, "ACCOUNT_NOT_FOUND", "Account was not found")
    return account
