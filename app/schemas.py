from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_serializer, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccountCreate(StrictModel):
    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: Decimal
    created_at: datetime

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return f"{value:.2f}"


class BalanceOut(BaseModel):
    account_id: int
    balance: Decimal

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return f"{value:.2f}"


class TransactionCreate(StrictModel):
    type: Literal["credit", "debit"]
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str
    reference_id: str = Field(min_length=1)


class TransferCreate(StrictModel):
    from_account_id: int = Field(gt=0, le=9_223_372_036_854_775_807)
    to_account_id: int = Field(gt=0, le=9_223_372_036_854_775_807)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str
    reference_id: str = Field(min_length=1)

    @field_validator("to_account_id")
    @classmethod
    def different_accounts(cls, value: int, info: ValidationInfo) -> int:
        from_account_id = getattr(info, "data", {}).get("from_account_id")
        if from_account_id == value:
            raise ValueError("source and destination accounts must differ")
        return value


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    type: Literal["credit", "debit"]
    amount: Decimal
    description: str
    reference_id: str
    created_at: datetime

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"


class PaginationOut(BaseModel):
    page: int
    limit: int
    total_records: int
    total_pages: int


class TransactionHistoryOut(BaseModel):
    data: list[TransactionOut]
    pagination: PaginationOut
