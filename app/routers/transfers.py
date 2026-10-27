from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import TransactionOut, TransferCreate
from app.services.transfer_service import transfer


router = APIRouter(tags=["transfers"])


@router.post("/transfers", status_code=201)
def post_transfer(
    body: TransferCreate, session: Session = Depends(get_session)
) -> dict[str, TransactionOut]:
    result = transfer(session, body)
    return {
        key: TransactionOut.model_validate(value, from_attributes=True)
        for key, value in result.items()
    }
