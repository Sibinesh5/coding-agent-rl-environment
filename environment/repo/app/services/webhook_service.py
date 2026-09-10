from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..domain import next_payment_status
from ..models import Inventory
from ..repositories.events import record_processed_event
from ..repositories.orders import get_order
from ..schemas import PaymentWebhook
from .audit import write_audit


def process_payment_webhook(db: Session, event: PaymentWebhook) -> None:
    order = get_order(db, event.order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    next_status = next_payment_status(order.status, event.event_type)

    if event.event_type == "payment.completed":
        inventory = db.get(Inventory, order.sku)
        if inventory is None or inventory.quantity < order.quantity:
            raise HTTPException(status_code=409, detail="insufficient inventory")
        inventory.quantity -= order.quantity
        db.add(inventory)
        db.commit()
        write_audit(db, order.id, event.event_id, "inventory_decremented")
    elif event.event_type == "payment.pending":
        write_audit(db, order.id, event.event_id, "order_pending")

    order.status = next_status
    order.last_event_sequence = event.sequence
    db.add(order)
    record_processed_event(
        db,
        event_id=event.event_id,
        order_id=order.id,
        event_type=event.event_type,
        sequence=event.sequence,
        applied=True,
    )
    db.commit()
