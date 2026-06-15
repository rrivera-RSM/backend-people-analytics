from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SalaryOfferCreateIn(BaseModel):
    employee_id: int = Field(gt=0)
    new_salary: float = Field(gt=0)
    new_bonus: float | None = Field(default=None, ge=0)
    month_payment_bonus: str | None = Field(default=None, max_length=20)
    bonus_next_fy: float | None = Field(default=None, ge=0)
    new_category: str | None = Field(default=None, max_length=100)
    observations: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "month_payment_bonus",
        "new_category",
        "observations",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def require_bonus_month(self) -> "SalaryOfferCreateIn":
        if self.new_bonus is not None and not self.month_payment_bonus:
            raise ValueError(
                "month_payment_bonus is required when new_bonus is provided"
            )
        return self


class SalaryOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    new_salary: float
    new_bonus: float | None = None
    month_payment_bonus: str | None = None
    bonus_next_fy: float | None = None
    new_category: str | None = None
    observations: str | None = None
    aud_user_creation: str
    aud_creation_at: datetime
