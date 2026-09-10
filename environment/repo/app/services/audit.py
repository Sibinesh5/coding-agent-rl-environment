from sqlalchemy.orm import Session
from ..models import AuditLog


def write_audit(db: Session, order_id: int, event_id: str, action: str) -> None:
    db.add(AuditLog(order_id=order_id, event_id=event_id, action=action))
