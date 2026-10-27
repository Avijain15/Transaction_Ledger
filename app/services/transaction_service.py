from math import ceil

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Account, Transaction
from app.schemas import TransactionCreate
from app.services.account_service import parse_account_id


def transaction_data(transaction: Transaction) -> dict[str, object]:
    return {
        "id": transaction.id,
        "account_id": transaction.account_id,
        "type": transaction.type,
        "amount": f"{transaction.amount:.2f}",
        "description": transaction.description,
        "reference_id": transaction.reference_id,
        "created_at": transaction.created_at,
    }


def duplicate_error(existing: Transaction) -> AppError:
    return AppError(
        409,
        "DUPLICATE_TRANSACTION",
        "A transaction with this reference id already exists for the account",
        [{"existing_transaction": transaction_data(existing)}],
    )


def add_transaction(
    session: Session, raw_account_id: str, body: TransactionCreate
) -> Transaction:
    account_id = parse_account_id(raw_account_id)
    try:
        with session.begin():
            account = session.scalar(
                select(Account).where(Account.id == account_id).with_for_update()
            )
            if account is None:
                raise AppError(404, "ACCOUNT_NOT_FOUND", "Account was not found")

            existing = session.scalar(
                select(Transaction).where(
                    Transaction.account_id == account_id,
                    Transaction.reference_id == body.reference_id,
                )
            )
            if existing is not None:
                raise duplicate_error(existing)

            if body.type == "debit" and account.balance < body.amount:
                raise AppError(422, "INSUFFICIENT_BALANCE", "Account balance is insufficient")

            transaction = Transaction(
                account_id=account_id,
                type=body.type,
                amount=body.amount,
                description=body.description,
                reference_id=body.reference_id,
            )
            account.balance += body.amount if body.type == "credit" else -body.amount
            session.add(transaction)
            session.flush()
            session.refresh(transaction)
        return transaction
    except IntegrityError as exc:
        existing = session.scalar(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.reference_id == body.reference_id,
            )
        )
        if existing is not None:
            raise duplicate_error(existing) from exc
        raise


def parse_pagination_value(raw_value: str, name: str, maximum: int | None = None) -> int:
    if not raw_value.isascii() or not raw_value.isdecimal():
        raise AppError(400, "INVALID_PAGINATION", f"{name} must be a positive integer")
    value = int(raw_value)
    if value < 1 or (maximum is not None and value > maximum):
        message = f"{name} must be between 1 and {maximum}" if maximum else f"{name} must be positive"
        raise AppError(400, "INVALID_PAGINATION", message)
    return value


def get_history(
    session: Session,
    raw_account_id: str,
    transaction_type: str | None,
    raw_page: str,
    raw_limit: str,
) -> dict[str, object]:
    account_id = parse_account_id(raw_account_id)
    if transaction_type not in (None, "credit", "debit"):
        raise AppError(400, "VALIDATION_ERROR", "type must be credit or debit")
    page = parse_pagination_value(raw_page, "page")
    limit = parse_pagination_value(raw_limit, "limit", 100)

    account_exists = session.scalar(select(Account.id).where(Account.id == account_id))
    if account_exists is None:
        raise AppError(404, "ACCOUNT_NOT_FOUND", "Account was not found")

    filters = [Transaction.account_id == account_id]
    if transaction_type is not None:
        filters.append(Transaction.type == transaction_type)
    total_records = session.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    items = session.scalars(
        select(Transaction)
        .where(*filters)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": ceil(total_records / limit),
        },
    }
