from sqlalchemy.orm import Session
from ..models import Order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def create_order(db: Session, sku: str, quantity: int) -> Order:
    order = Order(sku=sku, quantity=quantity, status="PENDING")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
