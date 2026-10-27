from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Account, Transaction
from app.schemas import TransferCreate
from app.services.transaction_service import duplicate_error


def transfer(session: Session, body: TransferCreate) -> dict[str, Transaction]:
    account_ids = sorted((body.from_account_id, body.to_account_id))
    try:
        with session.begin():
            locked_accounts = session.scalars(
                select(Account)
                .where(Account.id.in_(account_ids))
                .order_by(Account.id)
                .with_for_update()
            ).all()
            accounts = {account.id: account for account in locked_accounts}
            if len(accounts) != 2:
                raise AppError(404, "ACCOUNT_NOT_FOUND", "One or both accounts were not found")

            existing = session.scalar(
                select(Transaction)
                .where(
                    Transaction.account_id.in_(account_ids),
                    Transaction.reference_id == body.reference_id,
                )
                .order_by(Transaction.id)
            )
            if existing is not None:
                raise duplicate_error(existing)

            source = accounts[body.from_account_id]
            destination = accounts[body.to_account_id]
            if source.balance < body.amount:
                raise AppError(422, "INSUFFICIENT_BALANCE", "Source account balance is insufficient")

            debit = Transaction(
                account_id=source.id,
                type="debit",
                amount=body.amount,
                description=body.description,
                reference_id=body.reference_id,
            )
            credit = Transaction(
                account_id=destination.id,
                type="credit",
                amount=body.amount,
                description=body.description,
                reference_id=body.reference_id,
            )
            source.balance -= body.amount
            destination.balance += body.amount
            session.add_all([debit, credit])
            session.flush()
            session.refresh(debit)
            session.refresh(credit)
        return {"from_transaction": debit, "to_transaction": credit}
    except IntegrityError as exc:
        existing = session.scalar(
            select(Transaction)
            .where(
                Transaction.account_id.in_(account_ids),
                Transaction.reference_id == body.reference_id,
            )
            .order_by(Transaction.id)
        )
        if existing is not None:
            raise duplicate_error(existing) from exc
        raise
