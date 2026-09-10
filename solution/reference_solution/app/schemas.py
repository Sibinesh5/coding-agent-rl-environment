from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    quantity: int
    status: str
    last_event_sequence: int


class PaymentWebhook(BaseModel):
    event_id: str = Field(min_length=1)
    order_id: int = Field(gt=0)
    event_type: Literal["payment.pending", "payment.completed"]
    sequence: int = Field(gt=0)
